devenv:
	virtualenv -p python2.7 `pwd`/.venv
	. .venv/bin/activate && pip install -r requirements/development.txt

clean:
	rm -rvf .venv .tox .coverage build django-linguist* *.egg-info

pep8:
	flake8 linguist --ignore=E501,E127,E128,E124

test:
	coverage run --branch --source=linguist manage.py test linguist
	coverage report --omit=linguist/test*

serve:
	ENV=example python manage.py migrate && python manage.py runserver

delpyc:
	find . -name '*.pyc' -delete

release:
	python setup.py sdist register upload -s
