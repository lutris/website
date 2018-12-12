.PHONY: tags
setup:
	npm install
	npm run setup

watch:
	npm run watch

run:
	./manage.py runserver 0.0.0.0:8000

db:
	./manage.py migrate
	./manage.py loaddata accounts/fixtures/superadmin.json

clean:
	find . -name "*.pyc" -delete

cleanthumbs:
	./manage.py thumbnail clear
	./manage.py thumbnail cleanup
	rm -rf ./media/cache/

test:
	SEND_EMAILS=0 ./manage.py test --failfast $(test)

jenkins:
	./manage.py jenkins $(test)

sysdeps:
	sudo apt-get -y install libpq-dev python-dev nginx supervisor rabbitmq-server libjpeg-dev libxml2-dev libxslt1-dev
	pip install -r config/requirements/production.pip --exists-action=s

deps:
	pipenv install

check-deps-update:
	pipenv update --outdated

migration:
	-./manage.py makemigrations
	./manage.py migrate

fixtures:
	./manage.py dumpdata --indent=2 games > games/fixtures/initial_data.json

ctags:
	ctags -R --languages=python --python-kinds=-v ${VIRTUAL_ENV}/lib/python2.7
	ctags -R -a --languages=python --python-kinds=-v ${VIRTUAL_ENV}/src
	ctags -R -a --languages=python --python-kinds=-v .

deploy:
	fab -H lutris.net deploy

client:
	if [ -e lutris_client ]; then cd lutris_client; git pull; else git clone https://github.com/lutris/lutris lutris_client; fi

docs:
	rst2html.py --template=config/rst_template.txt lutris_client/docs/installers.rst > templates/docs/installers.html

shell:
	./manage.py shell_plus --traceback

worker:
	celery worker -A lutrisweb -B --loglevel=debug --hostname=lutris.net -E

sync:
	scp lutris.net:/srv/backup/sql/latest.tar.gz lutris.tar.gz
	gunzip lutris.tar.gz
	sudo -u postgres pg_restore --clean --dbname=lutris lutris.tar
	rm lutris.tar

tags:
	ctags -R .
