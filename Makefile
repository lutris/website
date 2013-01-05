run:
	./manage.py runserver

syncdb:
	./manage.py syncdb --noinput

test:
	./manage.py test

deps:
	pip install -r requirements.txt
