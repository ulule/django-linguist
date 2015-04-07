clean:
	rm -rvf .env .venv .tox .coverage build example/static/vendor django-linguist* *.egg-info

pep8:
	. .venv/bin/activate && flake8 linguist --ignore=E501,E127,E128,E124

test:
	. .venv/bin/activate && coverage run --branch --source=linguist manage.py test linguist
	. .venv/bin/activate && coverage report --omit=linguist/test*

serve:
	. .venv/bin/activate && ENV=example python manage.py syncdb
	. .venv/bin/activate && ENV=example python manage.py runserver

delpyc:
	find . -name '*.pyc' -delete

release:
	python setup.py sdist register upload -s
