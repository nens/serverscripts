Changelog of serverscripts
===================================================


0.9 (unreleased)
----------------

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
