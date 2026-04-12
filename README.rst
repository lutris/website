Getting the site up and running for development
===============================================

Install uv_, a fast Python package and virtualenv manager::

    curl -LsSf https://astral.sh/uv/install.sh | sh

.. _uv: https://docs.astral.sh/uv/

Clone the repository and install the Python dependencies::

    git clone https://github.com/lutris/website.git
    cd website
    uv sync

``uv sync`` creates a project-local ``.venv/`` and installs everything
from ``pyproject.toml``, including the ``dev`` dependency group
(ruff, pylint, coverage, ipdb, debug toolbar). System-level build
dependencies are still required to compile psycopg2, Pillow, and lxml::

    # Ubuntu / Debian
    sudo apt-get install build-essential git curl \
        imagemagick libxml2-dev libxslt1-dev libssl-dev \
        libffi-dev libpq-dev libjpeg-dev

    # Red Hat / Fedora
    sudo dnf install libpq-devel libxml2-devel libxslt-devel

Environment variables live in ``.env.local`` at the repository root.
Copy the sample below and fill in real values::

    DJANGO_SETTINGS_MODULE=lutrisweb.settings.local
    SECRET_KEY=changeme
    POSTGRES_DB=lutris
    POSTGRES_USER=lutris
    POSTGRES_PASSWORD=admin
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5434
    REDIS_HOST=localhost
    REDIS_PORT=6378
    STEAM_API_KEY=your_steam_api_key
    DISCORD_CLIENT_ID=your_discord_client_id
    DISCORD_CLIENT_SECRET=your_discord_client_secret

Export ``UV_ENV_FILE`` in your shell (or add it to a direnv ``.envrc``)
so that every ``uv run`` command below automatically loads the env
file::

    export UV_ENV_FILE=.env.local

All subsequent examples assume this is set. If you'd rather be explicit,
pass ``--env-file .env.local`` to each ``uv run`` invocation instead.

To build the frontend assets (javascript and css files), you'll
need Node and NPM available. If your distribution offers a version of
Node that is too old, you can use NVM (https://github.com/creationix/nvm)
to install a more recent version.

You can then build the frontend assets::

    npm install
    npm run build

To watch for file changes and recompile assets on the fly, you can run in a
separate terminal::

    npm run watch

Once your PostgreSQL database is configured (explained in the paragraph below),
run the database migrations to populate the database with tables::

    uv run ./manage.py migrate

You can create a new admin user with the command::

    uv run ./manage.py createsuperuser

Alternatively, if you want a database that is already populated with games,
there are snapshots on the Github releases page:
https://github.com/lutris/website/releases

The installer scripting documentation is not shipped with the website but
with the client, if you want to build the docs, you'll need to get the
client and compile the rst files into HTML. All this process is
automated::

    uv run make client
    uv run make docs

Once everything is set up correctly, you should be able to run the test
suite without any failures::

    uv run make test

Run the development server with::

    uv run make run

Redis configuration
===================

The lutris websites uses Redis as a cache. Install with::

    docker run -d \
        --name lutriscache \
        --restart unless-stopped \
        -p 6379:6379 \
        redis:latest


Postgresql configuration
========================

You can get the same Postgres server used in the Docker setup by running the
following command::

    docker run -d \
        --name lutrisdb \
        --restart unless-stopped \
        --shm-size 4gb \
        -e POSTGRES_PASSWORD=admin \
        -e POSGRES_DB=lutris \
        -e POSTGRES_USER=lutris \
        -p 5432:5432 \
        -v lutrisdb_backups:/backups \
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


Devcontainers
=============

VSCode is recommended as a primary IDE for development. It provides an out of the box support for `devcontainers` -
a modern full-featured development environment.

Prerequisite
------------

Latest version of VSCode with [devcontainers](https://code.visualstudio.com/docs/devcontainers/containers) extension and
Docker installed on your system.

After cloning the project choose the `Reopen in Container`` option from the VSCode menu.
The bootstrap process will run automatically during the initial execution, encompassing all the steps mentioned in this
tutorial.

Reset devcontainers env
-----------------------

- From the menu, opt for the `Reopen Folder Locally` choice.
- Wait until all containers have been stopped, which may take up to 10 seconds.
- Proceed to remove the SQL DB volume using the command:

    docker rm lutris-website_devcontainer_lutrisdb_1
    docker volume rm lutris-website_devcontainer_postgres_data

- Finally, select the `Rebuild and Reopen in Container` option from the VSCode menu.
