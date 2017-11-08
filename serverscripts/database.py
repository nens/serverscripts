"""Extract information from postgres databases.

"""
import argparse
import copy
import json
import logging
import os
import serverscripts
import subprocess
import sys

VAR_DIR = '/var/local/serverscripts'
POSTGRES_DIR = '/etc/postgres/sites-enabled'
OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'databases.fact')
DATABASE_TEMPLATE = {'name': '',
                     'size': 0}

logger = logging.getLogger(__name__)


def is_postgres_available():
    return os.path.exists('/etc/postgresql')


def _postgres_version():
    sub = subprocess.Popen('service postgresql status',
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)
    output, error = sub.communicate()
    # Output is something like "9.3/main (port 5432): online"
    parts = output.split('/')
    return parts[0]


def _database_infos():
    """Return dict with info about the databases {database name: info}"""
    query = ("select datname, pg_database_size(datname) "
             "from pg_database;")
    command = "sudo -u postgres psql -c '%s' --tuples-only" % query
    sub = subprocess.Popen(command,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)
    output, error = sub.communicate()
    if error:
        logger.warn("Error output from psql command: %s", error)
    result = {}
    for line in output.split('\n'):
        if not '|' in line:
            continue
        parts = line.split('|')
        name = parts[0].strip()
        size = parts[1].strip()  # in MB
        if name.startswith('template') or name == 'postgres':
            logger.debug("Omitting database %s", name)
            continue
        size = int(size)
        database_info = copy.deepcopy(DATABASE_TEMPLATE)
        database_info['name'] = name
        database_info['size'] = size
        result[name] = database_info
        logger.info("Found database %s with size %s (%s MB)",
                    name, size, size / 1024 / 1024)
    return result


def _table_bloat(database_names):
    query = """
-- btree index stats query
-- estimates bloat for btree indexes
WITH btree_index_atts AS (
    SELECT nspname,
        indexclass.relname as index_name,
        indexclass.reltuples,
        indexclass.relpages,
        indrelid, indexrelid,
        indexclass.relam,
        tableclass.relname as tablename,
        regexp_split_to_table(indkey::text, ' ')::smallint AS attnum,
        indexrelid as index_oid
    FROM pg_index
    JOIN pg_class AS indexclass ON pg_index.indexrelid = indexclass.oid
    JOIN pg_class AS tableclass ON pg_index.indrelid = tableclass.oid
    JOIN pg_namespace ON pg_namespace.oid = indexclass.relnamespace
    JOIN pg_am ON indexclass.relam = pg_am.oid
    WHERE pg_am.amname = 'btree' and indexclass.relpages > 0
         AND nspname NOT IN ('pg_catalog','information_schema')
    ),
index_item_sizes AS (
    SELECT
    ind_atts.nspname, ind_atts.index_name,
    ind_atts.reltuples, ind_atts.relpages, ind_atts.relam,
    indrelid AS table_oid, index_oid,
    current_setting('block_size')::numeric AS bs,
    8 AS maxalign,
    24 AS pagehdr,
    CASE WHEN max(coalesce(pg_stats.null_frac,0)) = 0
        THEN 2
        ELSE 6
    END AS index_tuple_hdr,
    sum( (1-coalesce(pg_stats.null_frac, 0)) * coalesce(pg_stats.avg_width, 1024) ) AS nulldatawidth
    FROM pg_attribute
    JOIN btree_index_atts AS ind_atts ON pg_attribute.attrelid = ind_atts.indexrelid AND pg_attribute.attnum = ind_atts.attnum
    JOIN pg_stats ON pg_stats.schemaname = ind_atts.nspname
          -- stats for regular index columns
          AND ( (pg_stats.tablename = ind_atts.tablename AND pg_stats.attname = pg_catalog.pg_get_indexdef(pg_attribute.attrelid, pg_attribute.attnum, TRUE))
          -- stats for functional indexes
          OR   (pg_stats.tablename = ind_atts.index_name AND pg_stats.attname = pg_attribute.attname))
    WHERE pg_attribute.attnum > 0
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
),
index_aligned_est AS (
    SELECT maxalign, bs, nspname, index_name, reltuples,
        relpages, relam, table_oid, index_oid,
        coalesce (
            ceil (
                reltuples * ( 6
                    + maxalign
                    - CASE
                        WHEN index_tuple_hdr%maxalign = 0 THEN maxalign
                        ELSE index_tuple_hdr%maxalign
                      END
                    + nulldatawidth
                    + maxalign
                    - CASE /* Add padding to the data to align on MAXALIGN */
                        WHEN nulldatawidth::integer%maxalign = 0 THEN maxalign
                        ELSE nulldatawidth::integer%maxalign
                      END
                )::numeric
              / ( bs - pagehdr::NUMERIC )
              +1 )
         , 0 )
      as expected
    FROM index_item_sizes
),
raw_bloat AS (
    SELECT current_database() as dbname, nspname, pg_class.relname AS table_name, index_name,
        bs*(index_aligned_est.relpages)::bigint AS totalbytes, expected,
        CASE
            WHEN index_aligned_est.relpages <= expected
                THEN 0
                ELSE bs*(index_aligned_est.relpages-expected)::bigint
            END AS wastedbytes,
        CASE
            WHEN index_aligned_est.relpages <= expected
                THEN 0
                ELSE bs*(index_aligned_est.relpages-expected)::bigint * 100 / (bs*(index_aligned_est.relpages)::bigint)
            END AS realbloat,
        pg_relation_size(index_aligned_est.table_oid) as table_bytes,
        stat.idx_scan as index_scans
    FROM index_aligned_est
    JOIN pg_class ON pg_class.oid=index_aligned_est.table_oid
    JOIN pg_stat_user_indexes AS stat ON index_aligned_est.index_oid = stat.indexrelid
),
format_bloat AS (
SELECT dbname as database_name, nspname as schema_name, table_name,
        round(realbloat) as bloat_pct, round(wastedbytes/(1024^2)::NUMERIC) as bloat_mb
FROM raw_bloat
)
-- final query outputting the bloated indexes
-- change the where and order by to change
-- what shows up as bloated
SELECT *
FROM format_bloat
WHERE ( bloat_pct > 20 and bloat_mb > 10 )
ORDER BY bloat_mb DESC;
    """
    command = "sudo -u postgres psql -c '%s' --tuples-only" % query
    sub = subprocess.Popen(command,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)
    output, error = sub.communicate()
    if error:
        logger.warn("Error output from psql command: %s", error)
    result = []
    for line in output.split('\n'):
        #  database_name | schema_name | table_name | bloat_pct | bloat_mb
        if '|' not in line:
            continue
        parts = [part.strip() for part in line.split('|')]
        name = ':'.join([parts[0].strip(), parts[1], parts[2]])
        percentage = parts[3]
        mb = parts[4]
        result.append({'name': name,
                       'percentage': percentage,
                       'mb': mb})
    return result


def all_info():
    """Return the info we want to extract from postgres + its databases"""
    result = {}
    result['version'] = _postgres_version()
    result['databases'] = _database_infos()
    database_names = [item['name'] for item in result['databases']]
    result['bloated_tables'] = _table_bloat(database_names)

    if result['databases']:
        # Info for zabbix.
        result['num_databases'] = len(result['databases'])
        sizes = [info['size'] for info in result['databases'].values()]
        result['total_databases_size'] = sum(sizes)
        result['biggest_database_size'] = max(sizes)

    return result


def main():
    """Installed as bin/checkout-info"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="Verbose output")
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        dest="print_version",
        default=False,
        help="Print version")
    options = parser.parse_args()
    if options.print_version:
        print(serverscripts.__version__)
        sys.exit()
    if options.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.WARN
    logging.basicConfig(level=loglevel,
                        format="%(levelname)s: %(message)s")

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)

    if not is_postgres_available():
        return

    result = all_info()
    open(OUTPUT_FILE, 'w').write(json.dumps(result, sort_keys=True, indent=4))

    zabbix_file = os.path.join(VAR_DIR, 'nens.num_databases.info')
    open(zabbix_file, 'w').write(str(result['num_databases']))
    zabbix_file = os.path.join(VAR_DIR, 'nens.total_databases_size.info')
    open(zabbix_file, 'w').write(str(result['total_databases_size']))
    zabbix_file = os.path.join(VAR_DIR, 'nens.biggest_database_size.info')
    open(zabbix_file, 'w').write(str(result['biggest_database_size']))
