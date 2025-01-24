Minard - SNO+ Monitoring from the Future
========================================

Quickstart
----------

To run a local copy of minard, first create a virtual environment and activate
it.

    $ virtualenv venv
    $ . venv/bin/activate

Now, clone the minard repository, and install the prerequisites:

    $ git clone git@github.com:EosDemonstrator/eos-minard.git
    $ cd minard
    $ pip install -r requirements.txt

Create a configuration file called settings.conf with the following values:

    DB_HOST='eos-db.localdomain'
    DB_PASS=[password]
    DB_USER='eos_user'
    DB_NAME='eos'
    DB_PORT=5432

Now, export the environment variable MINARD_SETTINGS to point to the
configuration file:

    $ export MINARD_SETTINGS=`pwd`/settings.conf

Now, you can start up the webserver:

    $ ./runserver.py

And you should be able to open your web browser to localhost:5000 and see it.

Note that you will probably see lots of errors since the flask app isn't able
to connect to the redis server. To install and run the redis server see
http://redis.io/topics/quickstart.
