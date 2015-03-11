django-linguist
===============

.. image:: https://secure.travis-ci.org/ulule/django-linguist.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/ulule/django-linguist

`django-linguist`_ is a Django_ application for flexible model translations.

Here a few principles that define this application in comparaison to others applications:

* Translations are stored in single one table and you can also use a different one per model
* No "one i18n table per model", say "goodbye" to nightmares :)
* No more painful migrations
* Not tied to model class names, you are free to use your own identifiers
* No ORM query hacks, it does not patch anything and it will be easier for you to upgrade your Django
* No magic, it uses metaclasses and mixins and everything is explicit
* Dead simple to plug in an existing project
* Django admin ready

If you are looking for a "one-i18n-table-per-model" way, `django-parler`_ is
an awesome alternative.

Installation
------------

.. code-block:: bash

    $ pip install django-linguist

In your ``settings.py``, add ``linguist`` to ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = (
        # Your other apps here
        'linguist',
    )

Then synchronize database:

.. code-block:: bash

    # >= Django 1.7
    $ python manage.py migrate linguist

    # < Django 1.7
    $ python manage.py syncdb

That's all.

Configuration
-------------

Models
~~~~~~

In three steps:

1. Add ``linguist.metaclasses.ModelMeta`` to your model as metaclass
2. Add ``linguist.mixins.ManagerMixin`` to your model manager
3. Add ``linguist`` settings in your model's Meta

Don't worry, it's fairly simple:

.. code-block:: python

    from django.db import models
    from django.utils.translation import ugettext_lazy as _

    from linguist.metaclasses import ModelMeta as LinguistMeta
    from linguist.mixins import ManagerMixin as LinguistManagerMixin


    class PostManager(LinguistManagerMixin, models.Manager):
        pass


    class Post(models.Model):

        __metaclass__ = LinguistMeta

        title = models.CharField(max_length=255)
        body = models.TextField()
        created_at = models.DateTimeField(auto_now_add=True)

        objects = PostManager()

        class Meta:
            verbose_name = _('post')
            verbose_name_plural = _('posts')
            linguist = {
                'identifier': 'can-be-anything-you-want',
                'fields': ('title', 'body'),
                'default_language': 'fr',
            }

The ``linguist`` meta requires:

* ``identifier``: a unique identifier for your model (can be anything you want)
* ``fields``: list or tuple of model fields to translate

And optionally requires:

* ``default_language``: the default language to use
* ``default_language_field``: the field that contains the default language to use (see below)
* ``decider``: the translation model to use instead of the default one (see below)

That's all. You're ready.

Default language per instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, you need to define default language at instance level. Linguist
supports this feature via the ``default_language_field`` option. Add a field
in your model that will store the default language then simply give the field
name to Linguist.

Let's take an example:

.. code-block:: python

    from django.db import models
    from django.utils.translation import ugettext_lazy as _

    from linguist.metaclasses import ModelMeta as LinguistMeta
    from linguist.mixins import ManagerMixin as LinguistManagerMixin


    class PostManager(LinguistManagerMixin, models.Manager):
        pass


    class Post(models.Model):

        __metaclass__ = LinguistMeta

        title = models.CharField(max_length=255)
        body = models.TextField()
        created_at = models.DateTimeField(auto_now_add=True)

        lang = models.CharField(max_length=5, default='en')

        objects = PostManager()

        class Meta:
            verbose_name = _('post')
            verbose_name_plural = _('posts')
            linguist = {
                'identifier': 'can-be-anything-you-want',
                'fields': ('title', 'body'),
                'default_language': 'en',
                'default_language_field': 'lang',
            }

Custom table for translations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, Linguist stores translations into ``linguist.models.Translation``
table. So in a single one table. If you need to use another table for a specific
model, Linguist provides a way to override this behavior: use *deciders*.

That's really easy to implement.

You can do it in three steps:

* Create a model that inherits from ``linguist.models.base.Translation``
* Don't forget to define it as concrete (``abstract = False`` in Meta)
* Give this model to Linguist meta ``decider`` option

This example will show you the light:

.. code-block:: python


    from django.db import models
    from django.utils.translation import ugettext_lazy as _

    from linguist.metaclasses import ModelMeta as LinguistMeta
    from linguist.mixins import ManagerMixin as LinguistManagerMixin
    from linguist.models.base import Translation


    # Our Post model decider
    class PostTranslation(Translation):
        class Meta:
            abstract = False


    class PostManager(LinguistManagerMixin, models.Manager):
        pass


    class Post(models.Model):

        __metaclass__ = LinguistMeta

        title = models.CharField(max_length=255)
        body = models.TextField()
        created_at = models.DateTimeField(auto_now_add=True)

        objects = PostManager()

        class Meta:
            verbose_name = _('post')
            verbose_name_plural = _('posts')
            linguist = {
                'identifier': 'can-be-anything-you-want',
                'fields': ('title', 'body'),
                'default_language': 'fr',
                'decider': PostTranslation,
            }

django.contrib.admin
~~~~~~~~~~~~~~~~~~~~

Simply use ``linguist.admin.ModelTranslationAdmin`` class:

.. code-block:: python

    from django.contrib import admin
    from linguist.admin import ModelTranslationAdmin
    from .models import Post


    class PostAdmin(ModelTranslationAdmin):
        list_display = ('title', 'body', 'created_at')


    admin.site.register(Post, PostAdmin)


Bonus! You can display instance's languages in ``list_display`` via the
``languages_column`` property provided by the admin class:

.. code-block:: python

    from django.contrib import admin
    from linguist.admin import ModelTranslationAdmin
    from .models import Post


    class PostAdmin(ModelTranslationAdmin):
        list_display = ('title', 'body', 'languages_column', 'created_at')


    admin.site.register(Post, PostAdmin)

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

``instance.active_language()``
    Set the current active language for the instance.

``instance.clear_translations_cache()``
    Remove all cached translations. Be aware, any content you set will be dropped.
    So no translation will be created/updated at saving.

.. code-block:: python

    # Let's create a new Post
    >>> post = Post()

    # Set English content
    >>> post.activate_language('en')
    >>> post.title = 'Hello'

    # Now set French content
    >>> post.activate_language('fr')
    >>> post.title = 'Bonjour'

    # Be sure everything works as expected for English
    >>> post.activate_language('en')
    >>> post.title
    Hello

    # And now for French
    >>> post.activate_language('fr')
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

.. code-block:: bash

    # Don't have pip?
    $ sudo easy_install pip

    # Don't already have virtualenv?
    $ sudo pip install virtualenv

    # Don't have Bower? Install Node.js for your OS then...
    $ sudo npm install -g bower

    # Clone and install dependencies
    $ git clone https://github.com/ulule/django-linguist.git
    $ cd django-linguist
    $ make install

    # Launch tests
    $ make test

    # Launch example project
    $ make serve

.. _django-linguist: https://github.com/ulule/django-linguist
.. _Django: http://djangoproject.com
.. _django-parler: https://github.com/edoburu/django-parler
