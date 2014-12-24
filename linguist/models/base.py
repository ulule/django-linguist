# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .. import settings


class TranslationManager(models.Manager):

    def save_cached(self, dicts):
        """
        Saves cached translations (cached in model instances as dictionaries).
        """
        to_create = []
        to_update = []
        bulk_create_objects = []

        # pk is None ? create object.
        # Otherwise, just update it
        for dct in dicts:
            pk = dct.get('pk', None)
            if pk is None:
                to_create.append(dct)
            else:
                to_update.append(dct)

        for dct in to_create:
            pk = dct.pop('pk', None)
            bulk_create_objects.append(self.model(**dct))

        if bulk_create_objects:
            self.bulk_create(bulk_create_objects)

        for dct in to_update:
            # Remove pk from fields to update
            pk = dct.pop('pk')
            self.filter(pk=pk).update(**dct)


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
        null=True,
        help_text=_('The object ID of this translation'))

    language = models.CharField(
        max_length=10,
        verbose_name=_('language'),
        choices=settings.SUPPORTED_LANGUAGES,
        default=settings.DEFAULT_LANGUAGE,
        help_text=_('The language for this translation'))

    field_name = models.CharField(
        max_length=100,
        verbose_name=_('field name'),
        help_text=_('The model field name for this translation.'))

    field_value = models.TextField(
        verbose_name=_('field value'),
        null=True,
        help_text=_('The translated content for the field.'))

    objects = TranslationManager()

    class Meta:
        abstract = True
        app_label = 'linguist'
        verbose_name = _('translation')
        verbose_name_plural = _('translations')
        unique_together = (('identifier', 'object_id', 'language', 'field_name'),)

    def __str__(self):
        return '%s:%s:%s:%s' % (
            self.identifier,
            self.object_id,
            self.field_name,
            self.language)
