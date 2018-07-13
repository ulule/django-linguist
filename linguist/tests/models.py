# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import six

from django.db import models

from linguist.models.base import Translation
from linguist.metaclasses import ModelMeta as LinguistMeta
from linguist.mixins import ManagerMixin as LinguistManagerMixin


# Managers
# ------------------------------------------------------------------------------
class TagManager(LinguistManagerMixin, models.Manager):
    """
    Manager of Tag model.
    """

    pass


class AuthorManager(LinguistManagerMixin, models.Manager):
    """
    Manager of Author model.
    """

    pass


class ArticleManager(LinguistManagerMixin, models.Manager):
    """
    Manager of Article model.
    """

    pass


class SlugManager(LinguistManagerMixin, models.Manager):
    """
    Manager of Slug model.
    """

    pass


class FileManager(LinguistManagerMixin, models.Manager):
    """
    Manager of File model.
    """

    pass


class FooManager(LinguistManagerMixin, models.Manager):
    """
    Manager of Foo model.
    """

    pass


class BarManager(LinguistManagerMixin, models.Manager):
    """
    Manager of Bar model.
    """

    pass


class DefaultLanguageFieldManager(LinguistManagerMixin, models.Manager):
    """
    Manager of DefaultLanguageFieldModel.
    """

    pass


class DeciderManager(LinguistManagerMixin, models.Manager):
    """
    Manager of DeciderModel
    """

    pass


# Models
# ------------------------------------------------------------------------------
class Tag(six.with_metaclass(LinguistMeta, models.Model)):
    name = models.CharField(max_length=255)

    objects = TagManager()

    class Meta:
        linguist = {"identifier": "tag", "fields": ("name",)}


class Author(six.with_metaclass(LinguistMeta, models.Model)):
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True)

    objects = AuthorManager()

    class Meta:
        linguist = {"identifier": "author", "fields": ("bio",)}


class Article(six.with_metaclass(LinguistMeta, models.Model)):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField(blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)

    objects = ArticleManager()

    class Meta:
        linguist = {"identifier": "article", "fields": ("title", "content")}


class SlugModel(six.with_metaclass(LinguistMeta, models.Model)):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    objects = SlugManager()

    class Meta:
        linguist = {"identifier": "slug", "fields": ("title",)}


class FileModel(six.with_metaclass(LinguistMeta, models.Model)):
    file = models.FileField(null=True, blank=True, upload_to="files")
    image = models.ImageField(null=True, blank=True, upload_to="images")

    objects = FileManager()

    class Meta:
        linguist = {"identifier": "file", "fields": ("file", "image")}


class FooModel(six.with_metaclass(LinguistMeta, models.Model)):
    """
    A foo.
    """

    title = models.CharField(max_length=255)
    excerpt = models.TextField(null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    position = models.PositiveIntegerField(null=True, blank=True)

    objects = FooManager()

    class Meta:
        linguist = {"identifier": "foo", "fields": ("title", "excerpt", "body")}


class BarModel(six.with_metaclass(LinguistMeta, models.Model)):
    """
    A bar.
    """

    title = models.CharField(max_length=255, null=True, blank=True)

    objects = BarManager()

    class Meta:
        linguist = {"identifier": "bar", "fields": ("title",)}


class DefaultLanguageFieldModel(six.with_metaclass(LinguistMeta, models.Model)):
    """
    A bar.
    """

    title = models.CharField(max_length=255, null=True, blank=True)
    lang = models.CharField(max_length=2, default="fr")

    objects = DefaultLanguageFieldManager()

    class Meta:
        linguist = {
            "identifier": "default_language_field_model",
            "fields": ("title",),
            "default_language_field": "lang",
        }


class DefaultLanguageFieldModelWithCallable(
    six.with_metaclass(LinguistMeta, models.Model)
):
    """
    A bar.
    """

    title = models.CharField(max_length=255, null=True, blank=True)
    lang = models.CharField(max_length=2, default="fr")

    objects = DefaultLanguageFieldManager()

    class Meta:
        verbose_name = "default_language_with_callable"
        linguist = {
            "identifier": "default_language_field_model",
            "fields": ("title",),
            "default_language_field": "language",
        }

    def language(self):
        return "fr"


class CustomTranslationModel(Translation):
    class Meta:
        abstract = False


class DeciderModel(six.with_metaclass(LinguistMeta, models.Model)):
    """
    Example of a model using decider feature.
    """

    title = models.CharField(max_length=255, null=True, blank=True)

    objects = DeciderManager()

    class Meta:
        linguist = {
            "identifier": "default_language_field_model",
            "fields": ("title",),
            "decider": CustomTranslationModel,
        }
