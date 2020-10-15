Getting the site up and running for development
===============================================
Docker is an open-source tool that automates the deployment of an application inside a software container. The easiest way to grasp the idea behind Docker is to compare it to, well... standard shipping containers.
===============================================
With docker-compose
-------------------

Install docker (https://docs.docker.com/engine/install/) and docker-compose (https://docs.docker.com/compose/install/) for your system.

To build the required docker images use::

    make build_dev_docker

Start the required containers with::

    make start_dev_docker

To prepare the database run in a separate terminal::

    make init_docker_db

You are now ready to develop. No need to rebuild the images for simple
code changes, as the containers will pick them up from the host system.
Operations requiring a rebuild:

- changing dependencies (apt, pip or npm)
- changing content of public/images, public/lightbox2 or public/robots.txt

You can stop the containers with::

    make stop_dev_docker

Natively
--------

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

Once your virtualenv is created, you can install the system and python
dependencies::

    sudo apt-get install build-essential git curl python3 python3-pip python3-dev imagemagick libxml2-dev libxslt1-dev libssl-dev libffi-dev libpq-dev libxml2-dev libjpeg-dev
    pip3 install -r config/requirements/devel.pip --exists-action=w

To build the frontend assets (javascript and css files), you'll
need Node and NPM available. If your distribution offers a version of
Node that is too old, you can use NVM (https://github.com/creationix/nvm)
to install a more recent version.

You can then build the frontend assets::

    npm install
    npm run setup
    run run build

To watch for file changes and recompile assets on the fly, you can run in a
separate terminal::

    npm run watch

The installer issues use another frontend stack based on VueJS. It is not
required to build them to work on other areas of the site. To build those
assets, run::

    cd frontend/vue
    npm install
    npm run build:issues  # for a production build
    npm run build:issues-dev  # for a development build and watch file changes

Once your PostgreSQL database is configured (explained in the paragraph below),
run the database migrations to populate the database with tables::

    ./manage.py migrate

You can create a new admin user with the command::

    ./manage.py createsuperuser

Alternatively, if you want a database that is already populated with games,
there are snapshots on the Github releases page:
https://github.com/lutris/website/releases

The installer scripting documentation is not shipped with the website but
with the client, if you want to build the docs, you'll need to get the
client and compile the rst files into HTML. All this process is
automated::

    make client
    make docs

Once everything is set up correctly, you should be able to run the test
suite without any failures::

    make test

Run the development server with::

    make run

Postgresql configuration
========================

You can get the same Postgres server used in the Docker setup by running the
following command::

    docker run -d \
        --name lutrisdb \
        --restart unless-stopped \
        -e POSTGRES_PASSWORD=admin \
        -e POSGRES_DB=lutris \
        -e POSTGRES_USER=lutris \
        -p 5432:5432 \
        postgres:12

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


Vue based code
--------------

Installer issues are using Vue based project stored in frontend/vue.

If you wish to develop for it, first install the dependencies and make a dev
build::

    cd frontend/vue
    npm install
    npm run build:issues-dev

The last command will run forever, watching for changes made to the
source and rebuilding the project on each update. Press Ctrl+C to interrupt it.
