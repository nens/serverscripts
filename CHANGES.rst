Changelog of serverscripts
===================================================


0.5 (unreleased)
----------------

- Nothing changed yet.


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
