# -*- coding: utf-8 -*-
from django.db import models

from .. import LinguistMeta, LinguistManagerMixin


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


class FooModel(models.Model):
    """
    A foo.
    """
    __metaclass__ = LinguistMeta

    title = models.CharField(max_length=255)
    excerpt = models.TextField(null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = FooManager()

    class Meta:
        linguist = {
            'identifier': 'foo',
            'fields': ('title', 'excerpt', 'body'),
        }


class BarModel(models.Model):
    """
    A bar.
    """
    __metaclass__ = LinguistMeta

    title = models.CharField(max_length=255, null=True, blank=True)

    objects = BarManager()

    class Meta:
        linguist = {
            'identifier': 'bar',
            'fields': ('title', ),
        }


class DefaultLanguageFieldModel(models.Model):
    """
    A bar.
    """
    __metaclass__ = LinguistMeta

    title = models.CharField(max_length=255, null=True, blank=True)
    lang = models.CharField(max_length=2, default='fr')

    objects = DefaultLanguageFieldManager()

    class Meta:
        linguist = {
            'identifier': 'default_language_field_model',
            'fields': ('title', ),
            'default_language_field': 'lang',
        }
