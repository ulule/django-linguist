install:
	@bower i
	@test -d .venv || virtualenv .venv
	@echo "source `pwd`/.venv/bin/activate" >> .env
	@. .venv/bin/activate && pip install -r requirements/development.txt

clean:
	@rm -rvf .env .venv .tox build example/static/vendor django-linguist* *.egg-info

pep8:
	flake8 linguist --ignore=E501,E127,E128,E124

test:
	coverage run --branch --source=linguist manage.py test linguist
	coverage report --omit=linguist/test*

release:
	python setup.py sdist register upload -s
