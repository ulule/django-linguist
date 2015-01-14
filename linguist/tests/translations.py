# -*- coding: utf-8 -*_
from django.db import models

from ..mixins import ModelMixin, ManagerMixin, ModelMeta


class FooManager(ManagerMixin, models.Manager):
    """
    Manager of Foo model.
    """
    pass


class BarManager(ManagerMixin, models.Manager):
    """
    Manager of Bar model.
    """
    pass


class FooModel(ModelMixin, models.Model):
    """
    A foo.
    """
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


class BarModel(ModelMixin, models.Model):
    """
    A bar.
    """
    title = models.CharField(max_length=255, null=True, blank=True)
    objects = BarManager()

    class Meta:
        linguist = {
            'identifier': 'bar',
            'fields': ('title', ),
        }
