Serverscripts: python scripts for sysadmin tasks on every linux server
======================================================================

This is a dependency-less python package that should be installed on all the
N&S linux servers. It contains python scripts for sysadmin tasks.

All scripts should be reasonably well-behaved including ``-h/--help``,
``--version`` and ``-v/--verbose`` options.


Installation
------------

TODO. Build python package locally. Scp somewhere. As root, ``pip install
URL``.


Cifsfixer
---------

Script that monitors the cifs mounts. If one isn't mounted, it mounts it. If
one isn't listable, it unmounts it (lazily if needed) and later tries to
re-mount it.

Should be installed in a cronjob.
