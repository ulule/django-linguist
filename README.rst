django-linguist
===============

.. image:: https://secure.travis-ci.org/ulule/django-linguist.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/ulule/django-linguist

Installation
------------

.. code-block:: bash

    $ pip install django-linguist

Usage
-----

Add ``linguist`` to your ``INSTALLED_APPS`` in ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = (
        # ...
        'linguist',
    )

Development
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

    $ git clone https://github.com/ulule/django-devbox.git
    $ cd django-devbox
    $ vagrant up
    $ vagrant package --base ulule_django_devbox --output ulule-django-devbox.box
    $ mkdir ~/vboxes
    $ mv ulule-django-devbox.box ~/vboxes/django_linguist.box
    $ vagrant up && vagrant ssh
    $ cd /vagrant
    $ make install
    $ source .venv/bin/activate

Tests
~~~~~

.. code-block:: bash

    $ vagrant up && vagrant ssh
    $ cd /vagrant
    $ make test
