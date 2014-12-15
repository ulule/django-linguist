# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from linguist.mixins import LinguistMixin


class Category(models.Model, LinguistMixin):
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(_('title'), max_length=255)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')


class Post(models.Model, LinguistMixin):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(_('title'), max_length=255)
    body = models.TextField(blank=True)
    category = models.ForeignKey(Category, blank=True, null=True)

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
