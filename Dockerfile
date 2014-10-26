FROM python:2.7

# Dependencies
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get install -y build-essential apt-utils
RUN apt-get install -y imagemagick memcached mercurial bzr

# virtualenvwrapper
RUN pip install virtualenvwrapper
RUN echo "source /usr/local/bin/virtualenvwrapper.sh" > /.bashrc

# Environmental Variables
ENV WORKON_HOME /root/.virtualenvs
ENV PROJECT_HOME /app
ENV DJANGO_SETTINGS_MODULE lutrisweb.settings.local
ENV USE_SQLITE 1

# Node.js
RUN curl -sL https://deb.nodesource.com/setup | bash -
RUN apt-get install -y nodejs
RUN npm install -g bower grunt-cli

# Mount the application directory
VOLUME ["/app"]
WORKDIR /app

# Set up the command interface
CMD ["-"]
ENTRYPOINT ["make"]
