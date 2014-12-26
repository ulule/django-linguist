# -*- coding: utf-8 -*-
import copy

from django.db import models, IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .. import settings


class TranslationManager(models.Manager):

    @staticmethod
    def _get_object_lookup(obj, language=None):
        """
        Returns object's lookup (for filter() method).
        """
        lookup = {
            'identifier': obj.linguist_identifier,
            'object_id': obj.pk,
        }

        if language is not None:
            lookup['language'] = language

        return lookup

    def get_object_translations(self, obj, language=None):
        """
        Shorcut method to retrieve translations for a given object.
        """
        lookup = self._get_object_lookup(obj, language)
        return self.get_queryset().filter(**lookup)

    def delete_object_translations(self, obj, language=None):
        """
        Shortcut method to delete translations for a given object.
        """
        self.get_object_translations(obj, language).delete()

    def get_languages(self):
        """
        Returns all available languages.
        """
        return (self.get_queryset()
                    .values_list('language', flat=True)
                    .distinct()
                    .order_by('language'))

    def save_cached(self, dicts):
        """
        Saves cached translations (cached in model instances as dictionaries).
        """
        to_create = []
        to_update = []
        bulk_create_objects = []

        # is_new is True? create object.
        # Otherwise, just update it
        for dct in dicts:
            is_new = dct.get('is_new', False)
            if is_new:
                to_create.append(dct)
            else:
                to_update.append(dct)

        for dct in to_create:
            new_dct = copy.copy(dct)
            del new_dct['is_new']
            bulk_create_objects.append(self.model(**new_dct))

        created = True
        if bulk_create_objects:
            try:
                self.bulk_create(bulk_create_objects)
            except IntegrityError:
                created = False

        if created:
            for dct in to_create:
                dct['is_new'] = False

        for dct in to_update:
            new_dct = copy.copy(dct)
            del new_dct['is_new']
            lookup = {}
            lookup['identifier'] = new_dct['identifier']
            lookup['object_id'] = new_dct['object_id']
            lookup['language'] = new_dct['language']
            self.filter(**lookup).update(**new_dct)


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
