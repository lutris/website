setup:
	npm install
	bower install
	grunt
run:
	./manage.py runserver

db:
	./manage.py syncdb --noinput
	./manage.py migrate
	./manage.py loaddata accounts/fixtures/superadmin.json

clean:
	find . -name "*.pyc" -delete

cleanthumbs:
	./manage.py thumbnail clear
	./manage.py thumbnail cleanup
	rm -rf ./media/cache/

test:
	./manage.py test --noinput $(test)

deps:
	pip install -r config/requirements.pip --exists-action=s

migration:
	-./manage.py schemamigration games --auto
	-./manage.py schemamigration common --auto
	-./manage.py schemamigration accounts --auto
	./manage.py migrate

fixtures:
	./manage.py dumpdata --indent=2 games > games/fixtures/initial_data.json

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
	./manage.py shell --traceback

worker:
	celery -A lutrisweb worker --loglevel=debug --autoreload --hostname=lutris.net -E

legacydump:
	./manage.py dumpdata --indent=2 -e accounts.Profile -e registration > lutrisweb.json
	sed -i 's/auth.user/accounts.user/' lutrisweb.json

sqlflush:
	./manage.py sqlflush | psql -U lutris_staging -h localhost lutris_staging

sqlsequencereset:
	./manage.py sqlsequencereset auth > sqlsequencereset.sql
	./manage.py sqlsequencereset thumbnail >> sqlsequencereset.sql
	./manage.py sqlsequencereset accounts >> sqlsequencereset.sql
	./manage.py sqlsequencereset admin >> sqlsequencereset.sql
	./manage.py sqlsequencereset django_openid_auth >> sqlsequencereset.sql
	./manage.py sqlsequencereset django_select2 >> sqlsequencereset.sql
	./manage.py sqlsequencereset djcelery >> sqlsequencereset.sql
	./manage.py sqlsequencereset games >> sqlsequencereset.sql
	./manage.py sqlsequencereset mithril >> sqlsequencereset.sql
	./manage.py sqlsequencereset south >> sqlsequencereset.sql
	./manage.py sqlsequencereset tastypie >> sqlsequencereset.sql
	cat sqlsequencereset.sql | psql -U lutris_staging -h localhost lutris_staging
