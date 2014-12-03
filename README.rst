django-linguist
===============

.. image:: https://secure.travis-ci.org/ulule/django-linguist.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/ulule/django-linguist

Installation
------------

.. code-block:: bash

    $ git clone https://github.com/ulule/django-linguist.git
    $ cd django-linguist
    $ python setup.py install

Usage
-----

Add ``linguist`` to your ``INSTALLED_APPS`` in ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = (
        # ...
        'linguist',
    )
