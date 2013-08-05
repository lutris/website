
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

    sudo apt-get install imagemagick memcached libmemcached-dev

* Install a recent version of nodejs and LessCSS 1.3.3. On Fedora, you can
  install the nodejs from the repos.

    sudo add-apt-repository ppa:chris-lea/node.js
    sudo npm install less@1.3.3 -g

* Make the SQLite database

    make db

* Get the source code for the Lutris client, this will allow to build the installer's docs.

    make client

* Make sure that everything is in order and run the test suite.

    make test

* Run the dev server and start coding

    make run
    firefox http://localhost:8000
