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

0.1 test release::

    $ bin/fullrelease

This prints a /tmp dir where the dist has been made. Scp that::

    $ scp /that/tmp/dir/dist/serverscripts-0.1.tar.gz vanrees.org:www/download/

And on a server, as root:

    $ pip install http://reinout.vanrees.org/download/serverscripts-0.1.tar.gz

You could also copy the tgz directly to the server and ``pip install the/file.tgz``.


Prerequisite: ``apt-get install python-pip``.



Cifsfixer
---------

Script that monitors the cifs mounts. If one isn't mounted, it mounts it. If
one isn't listable, it unmounts it (lazily if needed) and later tries to
re-mount it.

Should be installed in a cronjob. Suggestion for the crontab (note: it needs
to run as root)::

    */5 * * * * /usr/local/bin/cifsfixer > /dev/null 2>&1

It logs to ``/var/log/cifsfixer.log``. It automatically rotates the file
itself if it gets too large. Note: if everything is OK, there is no output in
the logfile. If you want to check if the tool runs OK, run it with
``--verbose``.
