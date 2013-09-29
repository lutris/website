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
	if [ -e lutris_client ]; then cd lutris_client; bzr pull; else bzr branch lp:lutris lutris_client; fi

docs:
	rst2html.py --template=config/rst_template.txt lutris_client/docs/installers.rst > templates/docs/installers.html

shell:
	./manage.py shell --traceback

worker:
	./manage.py celery worker --loglevel=debug --autoreload -E -Q celery,lutris
