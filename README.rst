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

And on a server, as root::

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


Checkout-info
-------------

``bin/checkout-info`` collects info on git checkouts and saves it as
``/var/local/serverinfo-facts/checkouts.fact``. This is used by serverinfo. It
contains information like git repo url, python packages+versions, master or
tag checkout and so on.

Should be installed in a cronjob. Suggestion for the crontab (note: it needs
to run as root)::

    */5 * * * * /usr/local/bin/checkout-info > /dev/null 2>&1


Rabbitmq-checker
----------------

``bin/rabbitmq-checker`` The script checks the length of messages per queue and
amount of the queues per vhost. When the limit of queues or messages is reached it
saves warnings in ``/var/local/serverscripts/nens.rabbitmq.message`` and a number of
warnings to ``/var/local/serverscripts/nens.num_rabbitmq_too_big.warnings``.
The configuration file is optionally in ``/etc/serverscripts/rabbitmq_zabbix.json``,
for example see ``tests/example_rabbitmq_zabbix.json``. If configuration is not
specified the scritp uses defaults values, queues=100 and messages=200.

configuration::

  {
    'lizard-nxt': { // vhost in rabbitmq
        'queues_limit': 10,
        'messages_limit': 300
        },
    ...
  }

Retrieve vhosts on rabbitmq-server::

    $ sudo rabbitmqctl list_vhosts


Before the taking it in production run the file manually in debug mode like::

    $ sudo bin/rabbitmq-checker -v



TODO/ideas
----------

- Jenkins integration, test coverage.

- zest.releaser plugin (google for it first!) for uploading the sdist
  somewhere non-vanrees-like.

- nginx info grabber, /srv django info grabber. Resurrect it from ye olde
  serverinfo tool.

- Figure out how to feed it to ansible's info collection machinery.

- Prepare info for zabbix.
