watch:
	npm run watch

run:
	./manage.py runserver 0.0.0.0:8000

deps:
	pip install -r config/requirements/devel.pip --exists-action=w

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

client:
	if [ -e lutris_client/.git ]; then cd lutris_client; git pull; else git clone https://github.com/lutris/lutris lutris_client; fi

docs:
	rst2html.py --template=config/rst_template.txt lutris_client/docs/installers.rst > templates/docs/installers.html

shell:
	./manage.py shell_plus --traceback

worker:
	celery -A lutrisweb worker -B --loglevel=debug --hostname=lutris.net -E

localdb:
	# Create a local Postgres database for development
	docker volume create lutrisdb_backups
	docker run --name lutrisdb -e POSTGRES_PASSWORD=admin -e POSTGRES_DB=lutris -e POSTGRES_USER=lutris -p 5432:5432 -d -v lutrisdb_backups:/backups --shm-size 4gb --restart=unless-stopped postgres:12

localredis:
	docker run --name lutriscache -p 6378:6379 -d --restart=unless-stopped redis:latest

syncdb:
	# Syncs the production database to the local db
	scp anaheim:/home/strider/volumes/lutris-sqldumps/latest.tar.gz latest.tar.gz
	gunzip latest.tar.gz
	docker cp latest.tar lutrisdb:/backups
	docker exec lutrisdb pg_restore -U lutris --clean --dbname=lutris /backups/latest.tar
	rm latest.tar

syncmedia:
	rsync -avz anaheim:/srv/prod/website/media/ media/

discord:
	# Load Discord App IDS to database
	./manage.py load_discord_apps discord-app-ids.json

snapshotdb:
	docker exec lutrisdb pg_dump --format=tar -U lutris lutris > snapshot.tar
