
Getting the site up and running for development

* Install virtualenvwrapper

    sudo pip install virtualenvwrapper

  If you run into problems with recent versions of Ubuntu, install it from the repos:

    sudo apt-get install virtualenvwrapper

* Configure your zshrc / bashrc to support virtualenvwrapper, add:

    ubuntu_venvwrapper="/etc/bash_completion.d/virtualenvwrapper"
    if [ -f $ubuntu_venvwrapper ]; then
        source $ubuntu_venvwrapper
    else
        virtualenv=$(which virtualenvwrapper.sh)
        if [ "$virtualenv" != "" ]; then
            source $virtualenv
        fi
    fi

* Create a virtualenv

    mkvirtualenv lutrisweb

* cd in the directory and set the virtualenv project path

    cd lutrisweb
    setvirtualenvproject

* Right after creating the lutris virtualenv, it should be activated (it should
  show the virtualenv name at the beginning of your bash / zsh prompt). Latter
  on to activate the environment, run:

    workon lutrisweb

* Once the virtualenv is activated, install the dependencies

    cdproject
    make deps

* Install the required system dependencies

    sudo apt-get install imagemagick memcached libmemcached-dev mercurial bzr python-dev

* Install a recent version of nodejs and grunt. On Fedora, you can
  install the nodejs from the repos. When nodejs and grunt are installed, you
  can install grunt dependencies for the project.
  Install bower components.

    sudo add-apt-repository ppa:chris-lea/node.js
    sudo apt-get install nodejs
    sudo npm install grunt-cli -g
    npm install
    bower install

* Make the SQLite database

    make db

* Get the source code for the Lutris client, this will allow to build the installer's docs.

    make client

* Make sure that everything is in order and run the test suite.

    make test

* Run the dev server and tell grunt to watch for changes in less / coffeescript
  files and start coding

    make run
    grunt watch
    firefox http://localhost:8000

Postgresql configuriguration
============================

Creating a database:

    create database lutris_staging with owner lutris_staging;

or (in shell)

    createdb lutris_staging -O lutris_staging

Modify database's owner:

    alter database lutris_staging owner to lutris_staging;

Change user's password:

    alter user lutris_staging with password 'admin';

Dropping all tables from the database
    
    drop schema public cascade;
    create schema public;
