# -*- coding: utf-8 -*-
import copy

from django.db import models
from django.db.models.fields import NOT_PROVIDED

from . import settings
from .models import Translation
from .utils.i18n import (get_cache_key,
                         build_localized_field_name,
                         get_language,
                         get_fallback_language)


def set_instance_cache(instance, translations):
    """
    Sets Linguist cache for the given instance.
    """
    for translation in translations:

        cache_key = get_cache_key(**dict(
            identifier=instance.linguist_identifier,
            object_id=instance.pk,
            language=translation.language,
            field_name=translation.field_name))

        if cache_key not in instance._linguist:
            instance._linguist[cache_key] = dict(
                    pk=translation.pk,
                    object_id=instance.pk,
                    identifier=instance.linguist_identifier,
                    language=translation.language,
                    field_name=translation.field_name,
                    field_value=translation.field_value)

    return instance


def get_translation_lookups(instance, fields=None, languages=None):
    """
    Returns a dict to pass to Translation.objects.filter().
    """
    lookups = dict(
        identifier=instance.linguist_identifier,
        object_id=instance.pk)

    if fields is not None:
        lookups['field_name__in'] = fields

    if languages is not None:
        lookups['language__in'] = languages

    return lookups


class ManagerMixin(object):
    """
    Linguist Manager Mixin.
    """

    def with_translations(self, fields=None, languages=None):
        """
        Prefetches translations.
        """
        for instance in self.get_queryset():
            lookups = get_translation_lookups(instance, fields, languages)
            translations = Translation.objects.filter(**lookups)
            set_instance_cache(instance, translations)


class ModelMixin(object):

    @property
    def linguist_identifier(self):
        """
        Returns Linguist's identifier for this model.
        """
        self._linguist.identifier

    @property
    def language(self):
        """
        Returns Linguist's current language.
        """
        return self._linguist.language

    @language.setter
    def language(self, value):
        """
        Sets Linguist's current language.
        """
        self._linguist.language = value

    @property
    def translatable_fields(self):
        """
        Returns Linguist's translation class fields (translatable fields).
        """
        return self._linguist.fields

    @property
    def available_languages(self):
        """
        Returns available languages.
        """
        return (Translation.objects
                           .filter(identifier=self.linguist_identifier, object_id=self.pk)
                           .values_list('language', flat=True)
                           .distinct()
                           .order_by('language'))

    def clear_translations_cache(self):
        """
        Clears Linguist cache.
        """
        self._linguist.clear()

    def get_translations_for_save(self):
        """
        Returns translation instances to save for the given model instance.
        """
        cache_keys = []

        for translatable_field in self.translatable_fields:
            for language_code, language_name in settings.SUPPORTED_LANGUAGES:
                cache_key_kwargs = dict(
                    identifier=self.linguist_identifier,
                    object_id=self.pk,
                    language=language_code,
                    field_name=translatable_field)
                cache_key = get_cache_key(**cache_key_kwargs)
                cache_keys.append(cache_key)

        return [self._linguist[k] for k in cache_keys if k in self._linguist]

    def save_translations(self):
        """
        Saves translations in the database.
        """
        Translation.objects.save_cached(self.get_translations_for_save())

    def save(self, *args, **kwargs):
        """
        Overwrites model's ``save`` method to save translations after instance
        has been saved (required to retrieve the object ID for ``Translation``
        model).
        """
        super(ModelMixin, self).save(*args, **kwargs)
        self.save_translations()
