clean:
	rm -rvf .env .venv .tox .coverage build example/static/vendor django-linguist* *.egg-info

pep8:
	flake8 linguist --ignore=E501,E127,E128,E124

test:
	coverage run --branch --source=linguist manage.py test linguist
	coverage report --omit=linguist/test*

serve:
	ENV=example python manage.py syncdb
	ENV=example python manage.py runserver

delpyc:
	find . -name '*.pyc' -delete

release:
	python setup.py sdist register upload -s
