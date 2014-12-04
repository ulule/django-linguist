# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .. import settings


@python_2_unicode_compatible
class Translation(models.Model):
    """
    A Translation.
    """
    identifier = models.CharField(
        max_length=100,
        verbose_name=_('identifier'),
        help_text=_('The registered model identifier.'))

    object_id = models.IntegerField(
        verbose_name=_('The object ID'),
        help_text=_('The object ID of this translation'))

    locale = models.CharField(
        max_length=10,
        verbose_name=_('locale'),
        choices=settings.SUPPORTED_LOCALES,
        default=settings.DEFAULT_LOCALE,
        help_text=_('The locale for this translation'))

    field_name = models.CharField(
        max_length=100,
        verbose_name=_('field name'),
        help_text=_('The model field name for this translation.'))

    content = models.TextField(
        verbose_name=_('content'),
        null=True,
        help_text=_('The translated content for the field.'))

    class Meta:
        abstract = True
        app_label = 'linguist'
        verbose_name = _('translation')
        verbose_name_plural = _('translations')
        unique_together = (('identifier', 'object_id', 'locale', 'field_name'),)

    def __str__(self):
        return '%s:%d:%s:%s' % (
            self.identifier,
            self.object_id,
            self.field_name,
            self.locale)
