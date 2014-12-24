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
then register them like this:

.. code-block:: python

    import linguist
    from .models import Post


    class PostTranslation(linguist.ModelTranslationBase):
        model = Post
        identifier = 'post_or_anything_else'
        fields = ('title', 'body')
        default_language = 'en'

    linguist.register(PostTranslation)

Translation classes are dead simple. You just have to define four class attributes:

* ``model``: the model to translate
* ``identifier``: a unique identifier for your model (can be anything you want)
* ``fields``: list or tuple of model fields to translate
* ``default_language``: the default language to use

And of course, you need to register them. Unregistered classes will be simply skipped.

Finally, add ``linguist.mixins.ModelMixin`` to your models:

.. code-block:: python

    from django.db import models
    from linguist.mixins import ModelMixin as LinguistModelMixin


    class Post(LinguistModelMixin, models.Model):
        title = models.CharField(max_length=255)
        body = models.TextField()


Then add ``linguist.mixins.ManagerMixin`` to your managers:

.. code-block:: python

    from django.db import models
    from linguist.mixins import ModelMixin as LinguistModelMixin
    from linguist.mixins import ManagerMixin as LinguistManagerMixin


    class PostManager(LinguistManagerMixin, models.Manager):
        pass


    class Post(LinguistModelMixin, models.Model):
        title = models.CharField(max_length=255)
        body = models.TextField()

        objects = PostManager()


Nothing more. You're ready.

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

The ``ModelMixin`` enhance your model with the following properties and methods:

``instance.linguist_identifier`` (*read-only* property)
    Your model identifier defined in the related translation class.
    Shortcut pointing on ``instance._linguist.identifier``.

``instance.language`` (*read-write* property)
    The current active language.
    Shortcut pointing on ``instance._linguist.language``.

``instance.default_language`` (*read-write* property)
    The default language to use.
    Shortcut pointing on ``instance._linguist.default_language``.

``instance.translatable_fields`` (*read-only* property)
    Translatable fields defined in the related translation class.
    Shorcut pointing on ``instance._linguist.fields``.

``instance.available_languages`` (*read-only* property)
    Available languages for this instance (content translated in these languages).

``instance.cached_translations_count`` (*read-only* property)
    Returns the number of cached translations. Each time you set a new language
    and set content on translatable fields, a cache is created for each language
    and field. It will be used to create ``Translation`` objets at instance saving.

``instance.clear_translations_cache()``
    Remove all cached translations. Be aware, any content you set will be dropped.
    So no translation will be created/updated at saving.

.. code-block:: python

    # Let's create a new Post
    >>> post = Post()

    # Set English content
    >>> post.language = 'en'
    >>> post.title = 'Hello'

    # Now set French content
    >>> post.language = 'fr'
    >>> post.title = 'Bonjour'

    # Be sure everything works as expected for English
    >>> post.language = 'en'
    >>> post.title
    Hello

    # And now for French
    >>> post.language = 'fr'
    >>> post.title
    Bonjour

    # Sweet! Save translations!
    >>> post.save()

To improve performances, you should prefetch translations:

.. code-block:: python

    >>> Post.objects.with_translations()

All translations will be cached in instances. Database won't be hit anymore.

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

Example Project
---------------

.. code-block:: bash

    $ vagrant up && vagrant ssh
    $ cd /vagrant
    $ ENV=example python manage.py syncdb
    $ ENV=example python manage.py runserver [::]:8000

Go to http://127.0.0.1:1337.
