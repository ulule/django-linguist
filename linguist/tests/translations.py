# -*- coding: utf-8 -*_
from django.db import models

from ..base import ModelTranslationBase
from ..mixins import ModelMixin, ManagerMixin


class FooManager(ManagerMixin, models.Manager):
    pass


class BarManager(ManagerMixin, models.Manager):
    pass


class FooModel(ModelMixin, models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = FooManager()


class FooTranslation(ModelTranslationBase):
    model = FooModel
    identifier = 'foo'
    fields = ('title', )


class BarModel(ModelMixin, models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    objects = BarManager()


class BarTranslation(ModelTranslationBase):
    model = BarModel
    identifier = 'bar'
    fields = ('title', )


class BadTranslation(object):
    pass


class BadModel(object):
    pass
