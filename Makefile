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
	pip install -r requirements.txt

migration:
	./manage.py schemamigration games --auto
	./manage.py migrate
