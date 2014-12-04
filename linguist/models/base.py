# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .. import compat
from ..utils import get_model_string


@python_2_unicode_compatible
class Translation(models.Model):
    """
    A Translation.
    """
    identifier = models.CharField(
        max_length=255,
        verbose_name=_('identifier'),
        help_text=_('The registered model identifier.'))

    locale = models.CharField(
        max_length=10,
        verbose_name=_('locale'),
        help_text=_('The locale'))

    column = models.CharField(
        max_length=255,
        verbose_name=_('identifier'),
        help_text=_('The identifier for the model.'))

    content = models.TextField(
        verbose_name=_('content'),
        null=True,
        help_text=_('The translated content.'))

    class Meta:
        abstract = True
        app_label = 'linguist'
        verbose_name = _('translation')
        verbose_name_plural = _('translations')
        unique_together = (('identifier', 'locale', 'column'),)

    def __str__(self):
        return '%s:%s (%s)' % (self.identifier, self.column, self.locale)
