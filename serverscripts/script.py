"""Run-everything script that collects all info.

Better than having 5 different cronjobs :-)"""

import serverscripts.apache
import serverscripts.checkouts
import serverscripts.database
import serverscripts.haproxy
import serverscripts.nginx


def main():
    """Run all info-gathering scripts

    Note: cifsfixer isn't run because the info-gathering is a side effect of
    the actual purpose of that script. We might want to move the
    info-gathering to a separate script, but for now it is OK. So... cifsfixer
    is run separately by another cronjob.

    """
    for module in [serverscripts.checkouts,
                   serverscripts.nginx,
                   serverscripts.apache,
                   serverscripts.database,
                   serverscripts.haproxy]:
        try:
            module.main()
        except Exception, e:
            print(e)
