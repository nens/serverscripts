Changelog of serverscripts
===================================================


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
