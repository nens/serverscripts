"""Run-everything script that collects all info.

Better than having 5 different cronjobs :-)"""

import serverscripts.apache
import serverscripts.checkouts
import serverscripts.database
import serverscripts.docker
import serverscripts.haproxy
import serverscripts.nginx
import serverscripts.pbis
import serverscripts.rabbitmq


def main():
    """Run all info-gathering scripts

    Note: cifsfixer isn't run because the info-gathering is a side effect of
    the actual purpose of that script. We might want to move the
    info-gathering to a separate script, but for now it is OK. So... cifsfixer
    is run separately by another cronjob.

    geoserver-info also isn't being run as it is quite expensive: it reads
    potentially huge nginx access log collections.

    """
    for module in [
        serverscripts.apache,
        serverscripts.checkouts,
        serverscripts.database,
        serverscripts.docker,
        serverscripts.haproxy,
        serverscripts.nginx,
        serverscripts.pbis,
        serverscripts.rabbitmq,
    ]:
        try:
            module.main()
        except Exception as e:
            print(e)
