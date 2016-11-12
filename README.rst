Getting the site up and running for development
===============================================

If you haven't done it already, install and configure virtualenvwrapper.
If you are unfamiliar with virtualenvwrapper, see their documentation on
their website: https://virtualenvwrapper.readthedocs.org/en/latest/

::

    mkvirtualenv lutrisweb
    cd lutrisweb
    setvirtualenvproject

Once the virtualenv is created, you need to make sure that some
environment variables are exported and are set to valid values, the
simplest way to achieve that is to edit the postactivate script in
`$VIRTUAL_ENV/lutrisweb/bin/postactivate` and add your exports here.
The only required environment varible is the DJANGO_SETTINGS_MODULE one::

    export DJANGO_SETTINGS_MODULE="lutrisweb.settings.local"

Optionnaly, if you don't want to setup a PostgreSQL database, you can
also tell the project to fallback to SQLite::

    export USE_SQLITE=1

Once your virtualenv is created, you can install the system and pyhton
dependencies::

    sudo apt-get install imagemagick memcached libmemcached-dev mercurial bzr python-dev
    make deps

In order to build the frontend code (javascript and css files), you'll
need nodejs, npm, grunt and bower installed on your system. If you are
running Ubuntu, it is advised to use nvm to get the most recent
version of node, you can install it following the instructions on the github
page ::

    https://github.com/creationix/nvm

Then install bower and grunt::

    npm install -g bower
    npm install -g grunt-cli

Once you have grunt and bower installed, you can run the following commands::

    make setup  # Will install the project's npm and bower dependencies
                # and build the static files
    grunt watch  # Watch for JS/CSS changes and compile them

You'll need to setup the database, if you want to use a PostgreSQL database,
follow the instructions found in the next paragraph before running this
command. The database setup will also create a superuser account with the
credentials admin/admin::

    make db

The installer scripting documentation is not shipped with the website but
with the client, if you want to build the docs, you'll need to get the
client and compile the rst files into HTML. All this process is
automated::

    make client
    make docs

Once everything is set up correctly, you should be able to run the test
suite without any failures::

    make test

You can now start developing on the website. Open your favorite editor and
run Django's internal web server::

    make run

Postgresql configuration
========================

Quickstart::

    sudo -u postgres psql
    create user lutris;
    create database lutris with owner lutris;
    alter user lutris createdb;
    alter database lutris owner to lutris;
    alter user lutris with password 'admin';

Create a user::

    sudo -u postgres create user lutris

Note that the user will need to be able to create databases in order to
run tests. If you have created an user without this permission, run::

    sudo -u postgres psql
    ALTER USER lutris CREATEDB;

Creating a database::

    sudo -u postgres psql
    create database lutris with owner lutris;

or (in shell)::

    createdb lutris -O lutris

Modify database's owner::

    sudo -u postgres psql
    alter database lutris owner to lutris;

Change user's password::

    sudo -u postgres psql
    alter user lutris with password 'admin';

Dropping all tables from the database::

    drop schema public cascade;
    create schema public;

Backing up the database::

    pg_dump lutris > lutris.sql

Restoring a backup::

    psql lutris < lutris.sql

To automate backups, make sure the Unix user has superuser privileges on
PostgreSQL and run this script with cron::

    cd /srv/backup/sql
    backup_file="lutris-$(date +%Y-%m-%d-%H-%M).tar"
    pg_dump --format=tar lutris > $backup_file
    gzip $backup_file
