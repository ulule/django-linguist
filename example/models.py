# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from linguist.metaclasses import ModelMeta as LinguistMeta
from linguist.mixins import ManagerMixin as LinguistManagerMixin
from linguist.models.base import Translation as BaseTranslation


class CategoryManager(LinguistManagerMixin, models.Manager):
    """
    Category Manager
    """
    pass


class Category(models.Model):
    """
    A Category.
    """
    __metaclass__ = LinguistMeta

    name = models.CharField(_('title'), max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CategoryManager()

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        linguist = {
            'identifier': 'category',
            'fields': ('name', ),
        }


class PostManager(LinguistManagerMixin, models.Manager):
    """
    Post Manager
    """
    pass


class Post(models.Model):
    """
    A Post.
    """
    __metaclass__ = LinguistMeta

    title = models.CharField(_('title'), max_length=255)
    body = models.TextField(blank=True)
    category = models.ForeignKey(Category, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PostManager()

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        linguist = {
            'identifier': 'post',
            'fields': ('title', 'body'),
        }


class BookmarkManager(LinguistManagerMixin, models.Manager):
    """
    Bookmark Manager
    """
    pass


class BookmarkTranslation(BaseTranslation):
    """
    Bookmark translations.
    """
    class Meta:
        abstract = False
        verbose_name = _('bookmark translation')
        verbose_name_plural = _('bookmark translations')


class Bookmark(models.Model):
    """
    A Bookmark
    """
    __metaclass__ = LinguistMeta

    title = models.CharField(_('title'), max_length=255)
    url = models.URLField(_('URL'))
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = BookmarkManager()

    class Meta:
        verbose_name = _('bookmark')
        verbose_name_plural = _('bookmarks')
        linguist = {
            'identifier': 'bookmark',
            'fields': ('description', ),
            'decider': BookmarkTranslation,
        }
