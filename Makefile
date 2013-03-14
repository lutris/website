run:
	./manage.py runserver

db:
	./manage.py syncdb --noinput
	./manage.py migrate

clean:
	find . -name "*.pyc" -delete

test:
	./manage.py test

deps:
	pip install -r requirements.txt --exists-action=s --verbose

migration:
	./manage.py schemamigration games --auto
	./manage.py migrate

fixtures:
	./manage.py dumpdata --indent=2 games > games/fixtures/initial_data.json

ctags:
	ctags -R --languages=python --python-kinds=-v ${VIRTUAL_ENV}/lib/python2.7
	ctags -R -a --languages=python --python-kinds=-v ${VIRTUAL_ENV}/src
	ctags -R -a --languages=python --python-kinds=-v .

deploy:
	fab staging deploy
