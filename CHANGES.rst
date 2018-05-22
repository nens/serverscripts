Changelog of serverscripts
===================================================


1.5 (unreleased)
----------------

- Added checkout-info support for pipenv projects.

- Support 'access_log off;' in nginx configs.


1.4 (2017-11-21)
----------------

- Pbis info (whether it exists only, though) is exported to the serverinfo
  facts.


1.3 (2017-11-14)
----------------

- Fixed database version detection for postgres 9.5.


1.2 (2017-11-09)
----------------

- Added bin/pbis-info script which checks the pbis status for zabbix.


1.1 (2017-11-08)
----------------

- Added database bloat logging.


1.0.3 (2017-03-20)
------------------

- More corner cases.


1.0.2 (2017-03-20)
------------------

- Bugfix (corner case).


1.0.1 (2017-03-20)
------------------

- Bugfix (missing import).


1.0 (2017-03-20)
----------------

- Ignoring files (instead of the expected directories) and lost+found dir
  in /srv now.

- Added docker detection (number of active images/volumes/containers).



0.54 (2016-11-14)
-----------------

- Zapped check of global supervisor: this is handled differently now and
  really needs a change in the supervisorrecipe. The current checks only lead
  to false positives.


0.53 (2016-09-20)
-----------------

- Fixing vhosts=None case.


0.52 (2016-09-20)
-----------------

- Don't crash when the rabbitmq config file doesn't exist.


0.51 (2016-09-20)
-----------------

- Rabbitmq check now always writes to the output files.


0.50 (2016-08-18)
-----------------

- Set path to rabbitmqctl.


0.49 (2016-08-18)
-----------------

- Import rabbitmq module.


0.48 (2016-08-17)
-----------------

- Improved rabbitmq logging.


0.47 (2016-08-17)
-----------------

- Added rabbitmq queue size checker.


0.46 (2016-04-20)
-----------------

- Added a couple more cronjob-type exceptions for supervisor.


0.45 (2016-04-12)
-----------------

- Ignoring supervisor lines with 'cron' in them. They don't need to be
  running, they are just there to keep cronjobs from running into each other.
  (Convention worked out with Alexandr for two 'flooding' servers).


0.44 (2016-03-30)
-----------------

- Added try/except around apache/nginx config file reading. Catches
  non-working symlinks, for instance.
  [reinout]


0.43 (2016-03-29)
-----------------

- Typo fix.


0.42 (2016-03-29)
-----------------

- Working around matplotlib issue.
  [reinout]


0.41 (2016-03-29)
-----------------

- More robust 'diffsettings' handling.
  [reinout]


0.40 (2016-03-29)
-----------------

- Returning from "diffsettings" command if there's an error (and no output).
  [reinout]


0.39 (2016-03-29)
-----------------

- Ignoring symlinks in ``/srv/``.
  [reinout]

- Extracting number of not-running processes out of supervisorctl (both inside
  ``/srv/sitename`` as the global one (if present).
  [reinout]


0.38 (2016-03-23)
-----------------

- Excluding datetime lines from diffsettings, too.
  [reinout]


0.37 (2016-03-23)
-----------------

- More broad exclusion: '<' handles '<lambda>', '<unbound ...>' and so on.
  [reinout]


0.36 (2016-03-23)
-----------------

- Logging bugfix.
  [reinout]

- Also ignoring "<lambda>" functions in diffsettings output.
  [reinout]


0.35 (2016-03-23)
-----------------

- Compensating for possible "syntax error" warnings when parsing the
  diffsettings output. Lizard-ui used to add "layout.Action()" objects to the
  settings and the output thereof isn't parseable.
  [reinout]


0.34 (2016-03-23)
-----------------

- Recording number of failures of running 'bin/django' for zabbix.


0.33 (2016-03-23)
-----------------

- Better spatialite handling.
  [reinout]

- Don't run both bin/django, bin/python *and* bin/test if one of them is
  enough. Prefer ``bin/django``, then ``bin/test`` and last ``bin/python``.
  [reinout]


0.32 (2016-03-22)
-----------------

- Bugfix for undefined variable.
  [reinout]


0.31 (2016-03-22)
-----------------

- Extracting DB info from django sites.
  [reinout]


0.30 (2016-03-22)
-----------------

- Returning databases as dict instead of only a number (=size).
  [reinout]


0.29 (2016-03-22)
-----------------

- Added missing import so that database info is gathered on all servers.
  [reinout]


0.28 (2016-03-21)
-----------------

- Return database size in bytes. That looks way better in zabbix. Otherwise
  you get ``20.4 kMB`` or something like that.
  [reinout]


0.27 (2016-03-21)
-----------------

- Fixed actual error: wrongly-named option.
  [reinout]


0.26 (2016-03-21)
-----------------

- More fixing.
  [reinout]


0.25 (2016-03-21)
-----------------

- More logging.
  [reinout]


0.24 (2016-03-21)
-----------------

- Added bin/database-info script.
  [reinout]


0.23 (2016-03-21)
-----------------

- Extracting databases info from postgres, including postgres version and
  database sizes.
  [reinout]


0.22 (2016-03-17)
-----------------

- Writing string to file (instead of an int).
  [reinout]


0.21 (2016-03-17)
-----------------

- Writing number of duplicate apache/ngix sites to a zabbix-readable file.
  [reinout]


0.20 (2016-03-17)
-----------------

- Added ``bin/gather-all-info script`` so that we only need one cronjob
  instead of multiple ones.
  [reinout]


0.19 (2016-03-15)
-----------------

- Cifsfixer now additionally outputs its cifs knowledge as a fact file for
  serverinfo.
  [reinout]


0.18 (2016-03-15)
-----------------

- Working RotatingFileHandler import...
  [reinout]


0.17 (2016-03-15)
-----------------

- Including ``six.py``. We don't want **any** external dependency.
  [reinout]

- Extracting git info from ``/srv/`` directories even when there's no
  ``buildout.cfg``.
  [reinout]

- Extracting cifs options, for instance the username from the cifs credentials
  file, if available.
  [reinout]


0.16 (2016-03-03)
-----------------

- Extracting info from haproxy.
  [reinout]


0.15 (2016-03-02)
-----------------

- Deleting 'Python' key from the returned eggs. It is set, somehow, to the
  version we run serverscripts with. Instead of the python version we want to
  detect. This last one is stored under the lowercase 'python' key.
  [reinout]


0.14 (2016-03-02)
-----------------

- Better python version detection. It doesn't crash anymore when there's no
  result. And it reads both stderr and stdout. Python 2 and 3 differ which
  stream they output their version to...
  [reinout]


0.13 (2016-02-29)
-----------------

- Extracting protocol (http/https) for redirects, too.
  [reinout]


0.12 (2016-02-29)
-----------------

- Added apache/nginx redirect detection.
  [reinout]


0.11.1 (2016-02-26)
-------------------

- Fix: /etc/apache2/ instead of /etc/apache/...
  [reinout]


0.11 (2016-02-26)
-----------------

- Added ``bin/apache-info`` for apache detection. It mostly mimicks the nginx
  one.
  [reinout]


0.10 (2016-02-25)
-----------------

- Compatibility with python 2 (which we're installed as as long as we still
  have 12.04 machines...)
  [reinout]


0.9 (2016-02-25)
----------------

- Fix for multiple sites within one server section: using ``copy.deepcopy()``,
  otherwise we end up with multiple copies of only one site.
  [reinout]

- Better git url detection: the trailing ``.git`` is not mandatory anymore.
  [reinout]

- Extracting related local checkout and proxy to local port or remote server.
  [reinout]


0.8.3 (2016-02-25)
------------------

- Supporting lizard5 nginx regex magic.
  [reinout]


0.8.2 (2016-02-25)
------------------

- Syntax typo fix...
  [reinout]


0.8.1 (2016-02-25)
------------------

- Bugfix in bin/nginx-info; json doesn't accept tuples as keys.
  [reinout]


0.8 (2016-02-25)
----------------

- Started nginx-info-extractor.
  [reinout]


0.7 (2016-02-18)
----------------

- Fix for git url regex so that ``https`` urls (instead of only ``git@`` urls)
  are also accepted.
  [reinout]


0.6 (2016-02-18)
----------------

- Added ``bin/checkout-info`` that saves info on git checkouts.
  [reinout]


0.5 (2016-01-06)
----------------

- Just listing the directory itself (``ls -d /mnt/something``) as a test
  whether the mount is readable. Pipes were giving too many problems.
  [reinout]


0.4 (2016-01-05)
----------------

- Work around weird 'broken pipe' problem on some servers. See
  http://coding.derkeiler.com/Archive/Python/comp.lang.python/2004-06/3823.html
  [reinout]


0.3 (2016-01-05)
----------------

- Fixed ``ls`` command to be more friendly for large directories.
  [reinout]

- Added zabbix integration.
  [reinout]


0.2 (2015-12-29)
----------------

- Added bare-bones installation instructions.
  [reinout]

- Fixed regex: multiple spaces aren't a problem anymore.
  [reinout]


0.1 (2015-12-29)
----------------

- Added tests for reading fstab/mtab files.
  [reinout]

- Added cifschecker script for auto-remounting necessary cifs mounts.
  [reinout]

- Initial project structure created with nensskel 1.37.dev0.
  [reinout]
