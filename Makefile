devenv:
	virtualenv -p python2.7 `pwd`/.venv
	. .venv/bin/activate && pip install -r requirements/development.txt

clean:
	@(rm -rvf .venv .tox .coverage build django-linguist* *.egg-info)

pep8:
	@(flake8 linguist --ignore=E501,E127,E128,E124)

test:
	@(honcho run py.test -s --cov-report term --cov-config .coveragerc --cov=linguist --color=yes linguist/tests/ -k 'not concurrency')

serve:
	@(honcho run python manage.py migrate && honcho run python manage.py runserver)

delpyc:
	@(find . -name '*.pyc' -delete)

release:
	@(python setup.py sdist register upload -s)
