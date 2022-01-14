Serverscripts: python scripts for sysadmin tasks on every linux server
======================================================================

This is a dependency-less python package that should be installed on all the
N&S linux servers. It contains python scripts for sysadmin tasks.

All scripts should be reasonably well-behaved including ``-h/--help``,
``--version`` and ``-v/--verbose`` options.


Local development and testing
-----------------------------

To ensure we can test with various python 3 versions, we use "tox". To get our
hands on those python versions, we use
docker. https://github.com/fkrull/docker-multi-python has a handy dockerfile
with lots of python versions (thanks to the "deadsnakes" repository). So to
test everything::

  $ docker compose build
  $ docker compose run --rm script tox

Note that if you change something in the dependencies, you'll have to
re-create the virtualenvs::

  $ docker compose run --rm script tox --recreate

If you want to test agains just one of the environments, run something like
this::

  $ docker compose run --rm script tox -e py38


Installation on servers
-----------------------

We're installed by an ansible script (see the private "sysadminsable"
repository).

If you need to do it manually, pip-install it *as root* (with the correct
version number).

  # pip install https://github.com/nens/serverscripts/archive/1.6.0.tar.gz

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



Docker-info
------------

``bin/docker-info`` collects info on dockers and saves availability/activity to
``/var/local/serverinfo-facts/dockers.fact``. This is used by the serverinfo
website.

It also prepares info for zabbix: the number of active images, containers and
volumes.

Should be installed in a cronjob. Suggestion for the crontab (note: it needs
to run as root)::

    */5 * * * * /usr/local/bin/docker-info > /dev/null 2>&1
