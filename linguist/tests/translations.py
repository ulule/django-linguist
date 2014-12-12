# -*- coding: utf-8 -*_
from django.db import models

from ..base import ModelTranslationBase
from ..mixins import LinguistMixin

class FooModel(models.Model, LinguistMixin):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class FooTranslation(ModelTranslationBase):
    model = FooModel
    identifier = 'foo'
    fields = ('title', )


class BarModel(models.Model, LinguistMixin):
    title = models.CharField(max_length=255)


class BarTranslation(ModelTranslationBase):
    model = BarModel
    identifier = 'bar'
    fields = ('title', )


class BadTranslation(object):
    pass


class BadModel(object):
    pass
