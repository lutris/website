.PHONY: tags

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
	SEND_EMAILS=0 ./manage.py test --no-input --failfast $(test)

jenkins:
	./manage.py jenkins $(test)

migration:
	-./manage.py makemigrations
	./manage.py migrate

fixtures:
	./manage.py dumpdata --indent=2 games > initial_data.json

check-deps-update:
	pip3 list --outdated

deploy:
	fab -H lutris.net deploy

deploy_dev:
	DOCKER_HOST="ssh://strider@anaheim" COMPOSE_PROJECT_NAME=lutrisweb_dev POSTGRES_HOST_PORT=5434 HTTP_PORT=82 DEPLOY_ENV=staging docker-compose -f docker-compose.prod.yml up -d --remove-orphans --build

deploy_staging:
	DOCKER_HOST="ssh://strider@anaheim" COMPOSE_PROJECT_NAME=lutrisweb_staging POSTGRES_HOST_PORT=5433 HTTP_PORT=81 DEPLOY_ENV=prod docker-compose -f docker-compose.prod.yml up -d --remove-orphans --build

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

build_dev_docker:
	docker-compose build lutrisfrontend lutrisweb

start_dev_docker:
	docker-compose up -d lutrisdb lutriscache
	# Wait a bit for the cache and database to be ready
	sleep 5
	docker-compose up -d lutrisfrontend lutrisweb

stop_dev_docker:
	docker-compose down

init_docker_db:
	docker-compose run lutrisweb make db
