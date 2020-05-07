.PHONY: tags
setup:
	npm install
	npm run setup

watch:
	npm run watch

run:
	./manage.py runserver 0.0.0.0:8000

db: deps
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

builddeps:
	sudo apt install -y libpq-dev python3-dev libjpeg-dev libxml2-dev libxslt1-dev libffi-dev

serverdeps:
	sudo apt-get update
	sudo apt-get -y --allow-unauthenticated install nginx supervisor rabbitmq-server locales
	pip3 install -r config/requirements/production.pip --exists-action=s

deps:
	pip3 install -r config/requirements/devel.pip --exists-action=w

migration:
	-./manage.py makemigrations
	./manage.py migrate

fixtures:
	./manage.py dumpdata --indent=2 games > initial_data.json

check-deps-update:
	pip3 list --outdated

deploy:
	fab -H lutris.net deploy

deploy_staging:
	DOCKER_HOST="ssh://strider@anaheim" COMPOSE_PROJECT_NAME=lutrisweb_staging docker-compose -f docker-compose.prod.yml up -d

client:
	if [ -e lutris_client/.git ]; then cd lutris_client; git pull; else git clone https://github.com/lutris/lutris lutris_client; fi

docs:
	rst2html.py --template=config/rst_template.txt lutris_client/docs/installers.rst > templates/docs/installers.html

shell:
	./manage.py shell_plus --traceback

worker:
	celery worker -A lutrisweb -B --loglevel=debug --hostname=lutris.net -E

sync:
	scp lutris.net:/srv/backup/sql/latest.tar.gz lutris.tar.gz
	gunzip lutris.tar.gz
	pg_restore -h localhost -U lutris --clean --dbname=lutris lutris.tar
	rm lutris.tar
