SETTINGS=lutrisweb.settings.local


setup:
	npm install
	bower install
	grunt
run:
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py runserver

db:
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py syncdb --noinput
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py migrate
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py loaddata accounts/fixtures/superadmin.json

clean:
	find . -name "*.pyc" -delete

cleanthumbs:
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py thumbnail clear
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py thumbnail cleanup
	rm -rf ./media/cache/

test:
	DJANGO_SETTINGS_MODULE=lutrisweb.settings.tests ./manage.py test --noinput $(test)

sysdeps:
	sudo apt-get install postgresql-server-dev-9.1
	pip install -r config/production.pip --exists-action=s

deps:
	pip install -r config/requirements.pip --exists-action=s

migration:
	-DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py schemamigration games --auto
	-DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py schemamigration common --auto
	-DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py schemamigration accounts --auto
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py migrate

fixtures:
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py dumpdata --indent=2 games > games/fixtures/initial_data.json

ctags:
	ctags -R --languages=python --python-kinds=-v ${VIRTUAL_ENV}/lib/python2.7
	ctags -R -a --languages=python --python-kinds=-v ${VIRTUAL_ENV}/src
	ctags -R -a --languages=python --python-kinds=-v .

deploy:
	fab staging deploy

client:
	if [ -e lutris_client ]; then cd lutris_client; git pull; else git clone https://github.com/lutris/lutris lutris_client; fi

docs:
	rst2html.py --template=config/rst_template.txt lutris_client/docs/installers.rst > templates/docs/installers.html

shell:
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py shell --traceback

worker:
	celery -A lutrisweb worker --loglevel=debug --autoreload --hostname=lutris.net -E

legacydump:
	./manage.py dumpdata --indent=2 -e accounts.Profile -e registration > lutrisweb.json
	sed -i 's/auth.user/accounts.user/' lutrisweb.json

sqlflush:
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlflush | psql -U lutris_staging -h localhost lutris_staging

sqlsequencereset:
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlsequencereset auth > sqlsequencereset.sql
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlsequencereset thumbnail >> sqlsequencereset.sql
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlsequencereset accounts >> sqlsequencereset.sql
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlsequencereset admin >> sqlsequencereset.sql
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlsequencereset django_openid_auth >> sqlsequencereset.sql
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlsequencereset django_select2 >> sqlsequencereset.sql
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlsequencereset djcelery >> sqlsequencereset.sql
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlsequencereset games >> sqlsequencereset.sql
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlsequencereset mithril >> sqlsequencereset.sql
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlsequencereset south >> sqlsequencereset.sql
	DJANGO_SETTINGS_MODULE=${SETTINGS} ./manage.py sqlsequencereset tastypie >> sqlsequencereset.sql
	cat sqlsequencereset.sql | psql -U lutris_staging -h localhost lutris_staging
