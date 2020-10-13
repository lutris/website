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
	DJANGO_TESTS=1 ./manage.py test --no-input --failfast $(test)

jenkins:
	./manage.py jenkins $(test)

migration:
	-./manage.py makemigrations
	./manage.py migrate

fixtures:
	./manage.py dumpdata --indent=2 games > initial_data.json

check-deps-update:
	pip3 list --outdated

deploy_staging:
	scripts/deploy.sh staging anaheim

deploy_prod:
	scripts/deploy.sh prod anaheim
	DOCKER_HOST="ssh://strider@anaheim" COMPOSE_PROJECT_NAME=lutrisweb_prod POSTGRES_HOST_PORT=5435 HTTP_PORT=82 DEPLOY_ENV=prod docker-compose -f docker-compose.prod.yml restart lutrisnginx

migrate_prod:
	DOCKER_HOST="ssh://strider@anaheim" COMPOSE_PROJECT_NAME=lutrisweb_prod POSTGRES_HOST_PORT=5435 HTTP_PORT=82 DEPLOY_ENV=prod docker-compose -f docker-compose.prod.yml run lutrisweb ./manage.py migrate

migrate_staging:
	DOCKER_HOST="ssh://strider@anaheim" COMPOSE_PROJECT_NAME=lutrisweb_staging POSTGRES_HOST_PORT=5433 HTTP_PORT=81 DEPLOY_ENV=staging docker-compose -f docker-compose.prod.yml run lutrisweb ./manage.py migrate

remote_shell_staging:
	DOCKER_HOST="ssh://strider@anaheim" COMPOSE_PROJECT_NAME=lutrisweb_staging POSTGRES_HOST_PORT=5433 HTTP_PORT=81 DEPLOY_ENV=staging docker-compose -f docker-compose.prod.yml run lutrisweb bash

remote_shell_prod:
	DOCKER_HOST="ssh://strider@anaheim" COMPOSE_PROJECT_NAME=lutrisweb_prod POSTGRES_HOST_PORT=5435 HTTP_PORT=82 DEPLOY_ENV=prod docker-compose -f docker-compose.prod.yml run lutrisweb bash

client:
	if [ -e lutris_client/.git ]; then cd lutris_client; git pull; else git clone https://github.com/lutris/lutris lutris_client; fi

docs:
	rst2html.py --template=config/rst_template.txt lutris_client/docs/installers.rst > templates/docs/installers.html

shell:
	./manage.py shell_plus --traceback

worker:
	celery worker -A lutrisweb -B --loglevel=debug --hostname=lutris.net -E

localdb:
	# Create a local Postgres database for development
	docker volume create lutrisdb_backups
	docker run --name lutrisdb -e POSTGRES_PASSWORD=admin -e POSTGRES_DB=lutris -e POSTGRES_USER=lutris -p 5432:5432 -d -v lutrisdb_backups:/backups --restart=unless-stopped postgres:12

syncdb:
	# Syncs the production database to the local db
	scp anaheim:/home/strider/volumes/lutris-sqldumps/latest.tar.gz lutris.tar.gz
	gunzip lutris.tar.gz
	docker cp lutris.tar lutrisdb:/backups
	docker exec lutrisdb pg_restore -U lutris --clean --dbname=lutris /backups/lutris.tar
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
