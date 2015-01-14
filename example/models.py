# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from linguist.mixins import ModelMixin as LinguistModelMixin
from linguist.mixins import ManagerMixin as LinguistManagerMixin


class CategoryManager(LinguistManagerMixin, models.Manager):
    """
    Category Manager
    """
    pass


class PostManager(LinguistManagerMixin, models.Manager):
    """
    Post Manager
    """
    pass


class Category(LinguistModelMixin, models.Model):
    """
    A Category.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(_('title'), max_length=255)

    objects = CategoryManager()

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        linguist = {
            'identifier': 'category',
            'fields': ('name', ),
        }

class Post(LinguistModelMixin, models.Model):
    """
    A Post.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(_('title'), max_length=255)
    body = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, blank=True, null=True)

    objects = PostManager()

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        linguist = {
            'identifier': 'post',
            'fields': ('title', 'body'),
        }
