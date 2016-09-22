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
    from django.utils.six import with_metaclass
    from django.utils.translation import ugettext_lazy as _

    from linguist.metaclasses import ModelMeta as LinguistMeta
    from linguist.mixins import ManagerMixin as LinguistManagerMixin


    class PostManager(LinguistManagerMixin, models.Manager):
        pass


    class Post(with_metaclass(LinguistMeta, models.Model)):
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
    from django.utils.six import with_metaclass
    from django.utils.translation import ugettext_lazy as _

    from linguist.metaclasses import ModelMeta as LinguistMeta
    from linguist.mixins import ManagerMixin as LinguistManagerMixin


    class PostManager(LinguistManagerMixin, models.Manager):
        pass


    class Post(with_metaclass(LinguistMeta, models.Model)):
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
    from django.utils.six import with_metaclass
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


    class Post(with_metaclass(LinguistMeta, models.Model)):
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

Simply use ``linguist.admin.TranslatableModelAdmin`` class:

.. code-block:: python

    from django.contrib import admin
    from linguist.admin import TranslatableModelAdmin
    from .models import Post


    class PostAdmin(TranslatableModelAdmin):
        list_display = ('title', 'body', 'created_at')

    admin.site.register(Post, PostAdmin)


Bonus! You can display instance's languages in ``list_display`` via the
``languages_column`` property provided by the admin class:

.. code-block:: python

    from django.contrib import admin
    from linguist.admin import TranslatableModelAdmin
    from .models import Post


    class PostAdmin(TranslatableModelAdmin):
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

Preloading
----------

To improve performances, you can preload/prefetch translations.

For a queryset (your queryset must inherit from Linguist manager/queryset):

.. code-block:: python

    >>> Post.objects.with_translations()

For a list of objects (all your objects must inherit from Linguist model):

.. code-block:: python

    >>> from linguist.helpers import prefetch_translations
    >>> posts = list(Post.objects.all())
    >>> prefetch_translations(posts)

For an instance (it must inherit from Linguist model):

.. code-block:: python

    >>> post = Post.objects.first()
    >>> post.prefetch_translations()

All translations will be cached in instances. Database won't be hit anymore.

This preloading system takes three parameters:

* ``field_names``: list of translatable field names to filter on
* ``languages``: list of languages to filter on
* ``populate_missing``: boolean if you want to populate cache for missing translations (defaults to ``True``)
* ``chunks_length``: chunk limit for SELECT IN ids for translations

For example, we only want to prefetch post titles in English without populating missing
translations with an empty string:

.. code-block:: python

    >>> Post.objects.with_translations(field_names=['title'], languages=['en'], populate_missing=False)

It works the same for:

* QuerySet ``with_translations()``
* Helper ``prefetch_translations()``
* Instance method ``prefetch_translations()``

**What does "populating missing translations" mean?**

Simple. By default, when you prefetch translations, instances cache will be populated
with empty strings for all supported languages (see  ``settings``). For example, if
you have ``en``, ``fr`` and ``it`` as supported languages and only have English
translations, if you try to access other languages, an empty string will be returned
without any database hit:

.. code-block:: python

    >>> Post.objects.with_translations()
    >>> post.title_fr # no database hit here because
    ''

Now, if you explicitly set ``populate_missing`` to ``False``, if a translation
is not found, it will be fetched from database.

.. code-block:: python

    >>> Post.objects.with_translations(populate_missing=False)
    >>> post.title_fr # database hit here
    ''

Development
-----------

.. code-block:: bash

    # Don't have pip?
    $ sudo easy_install pip

    # Don't already have virtualenv?
    $ sudo pip install virtualenv

    # Clone and install dependencies
    $ git clone https://github.com/ulule/django-linguist.git
    $ cd django-linguist
    $ make devenv

    # Enable virtual environment.
    $ source .venv/bin/activate

    # Launch tests
    $ make test

    # Launch example project
    $ make serve

.. _django-linguist: https://github.com/ulule/django-linguist
.. _Django: http://djangoproject.com
.. _django-parler: https://github.com/edoburu/django-parler

Compatibility
-------------

- python 2.7: Django 1.8, 1.9, 1.10
- Python 3.4: Django 1.8, 1.9, 1.10
- Python 3.5: Django 1.8, 1.9, 1.10
