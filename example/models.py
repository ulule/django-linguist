# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Category(models.Model):
    name = models.CharField(_('title'), max_length=255)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')


class Post(models.Model):
    title = models.CharField(_('title'), max_length=255)
    body = models.TextField(blank=True)

    category = models.ForeignKey(
        Category,
        verbose_name=_('category'),
        null=True)

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
