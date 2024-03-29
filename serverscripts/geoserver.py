"""Extract information from geoserver

"""
from collections import Counter
from serverscripts.clfparser import CLFParser
from urllib.parse import parse_qs
from urllib.parse import urlparse

import argparse
import glob
import gzip
import json
import logging
import os
import serverscripts
import sys
import xml.etree.ElementTree as ET


OUTPUT_DIR = "/var/local/serverinfo-facts"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "geoserver.fact")
CONFIG_DIR = "/etc/serverscripts"
CONFIG_FILE = os.path.join(CONFIG_DIR, "geoserver.json")
EXTRACT_FROM_PARAM = "extract workspace from layer param"

logger = logging.getLogger(__name__)


def load_config(config_file_path):
    """Return configuration"""
    content = {}
    if not os.path.exists(config_file_path):
        return
    with open(config_file_path, "r") as config_file:
        try:
            content = json.loads(config_file.read())
        except:  # noqa: E722
            logger.exception("Faulty config file %s", config_file_path)
            return

    required_keys = ["geoserver_name", "logfile", "data_dir"]
    for info_per_geoserver in content:
        for required_key in required_keys:
            if required_key not in info_per_geoserver:
                logger.error("Required key %s missing in config file", required_key)
                return

    return content


def extract_from_line(line):
    # {'Referer': '"https://wpn.klimaatatlas.net/"',
    #  'Useragent': '"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) '
    #               'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.1 '
    #               'Safari/605.1.15"',
    #  'b': '1796',
    #  'h': '10.100.110.89',
    #  'l': '-',
    #  'r': '"GET '
    #       '/geoserver/klimaatatlas/wms?service=WMS&request=GetMap&layers=klimaatatlas%3Aoverzicht_gemeenten_met_ka&styles=&format=image%2Fpng&transparent=true&version=1.1.1&SRS=EPSG%3A3857&width=256&height=256&srs=EPSG%3A3857&bbox=626172.1357121639,6261721.357121641,939258.203568246,6574807.424977722 '
    #       'HTTP/1.1"',
    #  's': '200',
    #  't': '[15/Nov/2018:06:25:14 +0100]',
    #  'time': datetime.datetime(2018, 11, 15, 6, 25, 14),
    #  'timezone': '+0100',
    #  'u': '-'}
    clf = CLFParser.logDict(line)
    referer = clf["Referer"]
    if referer:
        referer_parts = referer.split("/")
        if len(referer_parts) >= 2:
            referer = referer_parts[2]
    if referer == '"-"':
        referer = None
    request = clf["r"]
    try:
        url = request.split()[1]
    except IndexError:
        logger.warn("Couldn't extract nginx logline: %s", line)
        return
    parsed_url = urlparse(url)
    path = parsed_url.path
    # '/geoserver/klimaatatlas/wms' OR '/geoserver/wms'
    if path == "/geoserver/wms":
        # workspace is embedded in the "layers" parameter, probably.
        workspace = EXTRACT_FROM_PARAM
    else:
        # Normal case, workspace embedded in the url.
        try:
            workspace = path.split("/")[2]  # 'klimaatatlas'
        except IndexError:
            # favicon.ico or something like that.
            return
    query = parse_qs(parsed_url.query)
    # {'SRS': ['EPSG:3857'],
    #  'bbox': ['0,7200979.560689885,313086.06785608194,7514065.628545967'],
    #  'format': ['image/png'],
    #  'height': ['256'],
    #  'layers': ['klimaatatlas:overzicht_gemeenten_met_ka'],
    #  'request': ['GetMap'],
    #  'service': ['WMS'],
    #  'srs': ['EPSG:3857'],
    #  'transparent': ['true'],
    #  'version': ['1.1.1'],
    #  'width': ['256']}
    layers = query.get("layers") or query.get("LAYERS")
    if not layers:
        # Not a regular wms request.
        return
    if workspace == EXTRACT_FROM_PARAM:
        # The workspace name is embedded in the layers with a colon:
        # nieuwegein_klimaatatlas:1844_nieuwegein_bluelabel_droogte,km_mask_nieuwegein
        layers_value = layers[0]  # The parsed result is always a list.
        if ":" not in layers_value:
            return
        workspace = layers_value.split(":")[0]
    return {
        "referer": referer,
        "workspace": workspace,
    }


def extract_from_logfiles(logfile):
    if not os.path.exists(logfile):
        return

    logfiles = glob.glob(logfile + "*")
    for logfile in logfiles:
        logger.debug("Reading logfile %s", logfile)
        if logfile.endswith(".gz"):
            f = gzip.open(logfile, "rt")
        else:
            f = open(logfile, "rt")
        for line in f:
            if "/geoserver/" not in line:
                continue
            if "GetMap" not in line:
                continue
            result = extract_from_line(line)
            if result:
                yield result
        f.close()


def get_text_or_none(element, tag):
    try:
        return element.find(tag).text
    except AttributeError:
        return None


def extract_datastore_info(datastore_file):
    logger.debug("Extracting info from %s...", datastore_file)
    root = ET.parse(datastore_file).getroot()
    result = {}
    result["type"] = get_text_or_none(root, "type")
    result["enabled"] = get_text_or_none(root, "enabled")
    connection = root.find("connectionParameters")
    if connection:
        result["database_server"] = get_text_or_none(connection, "./entry[@key='host']")
        if result["database_server"]:
            if "nens" in result["database_server"]:
                # Split off .nens or .external-nens.local
                result["database_server"] = result["database_server"].split(".")[0]
        result["database_name"] = get_text_or_none(
            connection, "./entry[@key='database']"
        )
        result["database_user"] = get_text_or_none(connection, "./entry[@key='user']")
        jndi_connection = get_text_or_none(
            connection, "./entry[@key='jndiReferenceName']"
        )
        if jndi_connection:
            result["database_name"] = jndi_connection

    return result


def _combine_with_comma(datastores, key):
    values = [datastore[key] for datastore in datastores if datastore[key]]
    return ", ".join(set(values))


def extract_from_dirs(data_dir):
    workspaces_dir = os.path.join(data_dir, "workspaces")
    datastore_files = glob.glob(workspaces_dir + "/*/*/datastore.xml")
    workspace_names = set(
        [datastore_file.split("/")[-3] for datastore_file in datastore_files]
    )
    result = {}
    for workspace_name in workspace_names:
        workspace = {}
        workspace_datastore_files = [
            datastore_file
            for datastore_file in datastore_files
            if datastore_file.split("/")[-3] == workspace_name
        ]
        datastores = [
            extract_datastore_info(workspace_datastore_file)
            for workspace_datastore_file in workspace_datastore_files
        ]
        for key in [
            "enabled",
            "type",
            "database_server",
            "database_user",
            "database_name",
        ]:
            workspace[key] = _combine_with_comma(datastores, key)
        result[workspace_name] = workspace

    return result


def extract_workspaces_info(geoserver_configuration):
    """Return list of workspaces with all info"""
    workspaces = {}
    datastores_info = extract_from_dirs(geoserver_configuration["data_dir"])

    workspace_names_and_referers = Counter(
        (
            (log_line["workspace"], log_line["referer"])
            for log_line in extract_from_logfiles(geoserver_configuration["logfile"])
        )
    ).most_common()

    workspace_names_counter = Counter()
    for (workspace_name, referer), workspace_count in workspace_names_and_referers:
        workspace_names_counter.update({workspace_name: workspace_count})
    workspace_names = workspace_names_counter.most_common()

    for workspace_name, workspace_count in workspace_names:
        if workspace_name not in datastores_info:
            logger.warn(
                "Workspace %s from nginx logfile is missing in workspaces dir.",
                workspace_name,
            )
            continue

        referers = Counter()
        for (found_workspace_name, referer), count in workspace_names_and_referers:
            if found_workspace_name != workspace_name:
                continue
            referers.update({referer: count})
        common_referers = [
            "%s (%d)" % (referer, count) for (referer, count) in referers.most_common(5)
        ]
        workspaces[workspace_name] = {
            "usage": workspace_count,
            "referers": " + ".join(common_referers),
        }

    result = []

    for workspace_name in datastores_info:
        if workspace_name not in workspaces:
            workspaces[workspace_name] = {"usage": "", "referers": ""}

    for workspace_name, workspace_info in workspaces.items():
        workspace_info["workspace_name"] = workspace_name
        workspace_info["geoserver_name"] = geoserver_configuration["geoserver_name"]
        info_from_datastore_files = datastores_info.get(workspace_name, {})
        workspace_info.update(info_from_datastore_files)
        result.append(workspace_info)

    return result


def main():
    """Installed as bin/geoserver-info"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="Verbose output",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        dest="print_version",
        default=False,
        help="Print version",
    )

    options = parser.parse_args()
    if options.print_version:
        print(serverscripts.__version__)
        sys.exit()
    if options.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.WARN
    logging.basicConfig(level=loglevel, format="%(levelname)s: %(message)s")

    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)
        logger.info("Created %s", CONFIG_DIR)

    configuration = load_config(CONFIG_FILE)
    if not configuration:
        return

    result_for_serverinfo = {}
    # The result is a dict of a list of dicts. Key is the geoserver name, the
    # list is a list of workspaces, every workspace is a dict with
    # geoserver_name, active, etc.  xxx
    for geoserver_configuration in configuration:
        workspaces = extract_workspaces_info(geoserver_configuration)
        result_for_serverinfo[geoserver_configuration["geoserver_name"]] = workspaces

    if not result_for_serverinfo:
        return

    open(OUTPUT_FILE, "w").write(
        json.dumps(result_for_serverinfo, sort_keys=True, indent=4)
    )
