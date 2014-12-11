django-linguist
===============

Installation
------------

.. code-block:: bash

    $ pip install django-linguist

In your ``settings.py``, add ``linguist`` to ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = (
        # other apps
        'linguist',
    )

Then synchronize database:

.. code-block:: bash

    $ python manage.py syncdb

That's all.

Configuration
-------------

Create a module named ``linguist_registry.py`` in your app :

.. code-block:: bash

    $ cd /path/to/your/django/app
    $ touch linguist_registry.py

Create a ``ModelTranslationBase`` class for each model you want to translate
then register them like this :

.. code-block:: python

    import linguist
    from .models import Post


    class PostTranslation(linguist.ModelTranslationBase):
        model = Post
        identifier = 'post_or_anything_else'
        fields = ('title', 'body')


    linguist.register(PostTranslation)

Translation classes are dead simple. You just have to define three class attributes:

* ``model``: the model to translate
* ``identifier``: a unique identifier for your model (can be anything you want)
* ``fields``: list or tuple of model fields to translate

And of course, you need to register them. Unregistered classes will be simply skipped.

How it works
------------

Linguist adds virtual language fields to your models. For the example above, if
we have ``en``, ``fr`` and ``it`` in ``settings.LANGUAGES``, it
dynamically adds the following fields in ``Post`` model:

* ``Post.title_en``
* ``Post.title_fr``
* ``Post.title_it``
* ``Post.body_en``
* ``Post.body_fr``
* ``Post.body_it``

These fields are virtuals. They don't exist in ``Post`` table. There are
wrappers around ``linguist.Translation`` model. All translations will be stored
in this table.

When you set/get ``post.title``, Linguist will use the current active language
and will set/get the correct field for this language. For example, if your
default language is English (``en``), then ``Post.title`` will refer to ``post.title_en``.

Linguist adds four new methods to your model instances:

* ``instance.get_current_language()``
* ``instance.set_current_language()``
* ``instance.linguist_clear_cache()``
* ``instance.prefetch_translations()``

Let's play with ``get_current_language()`` and ``set_current_language()``:

.. code-block:: python

    >>> post = Post()

    >>> post.get_current_language()
    en

    >>> post.title = 'Hello'
    >>> post.title
    Hello

    >>> post.set_current_language('fr')
    >>> post.title = 'Bonjour'
    >>> post.title
    Bonjour

    >>> post.set_current_language('en')
    >>> post.title
    Hello

    >>> post.title_en
    Hello

    >>> post.title_fr
    Bonjour

To improve performances, you should prefetch translations:

.. code-block:: python

    >>> post.prefetch_translations()

Now, all translations are cached in the instance. Database won't be hit.

You can clear the cache at anytime with:

.. code-block:: python

    >>> post.linguist_clear_cache()

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
