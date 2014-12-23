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
    Sets Linguist cache for the given instance with data from the given translations.
    """
    base_key = dict(identifier=instance._linguist.identifier, object_id=instance.pk)
    for translation in translations:
        key = dict(language=translation.language, field_name=translation.field_name)
        key.update(base_key)
        cache_key = get_cache_key(**key)
        if cache_key not in instance._linguist:
            instance._linguist[cache_key] = translation
    return instance


def get_translation_lookups(instance, fields=None, languages=None):
    """
    Returns a dict to pass to Translation.objects.filter().
    """
    lookups = dict(identifier=instance.identifier, object_id=instance.pk)
    if fields is not None:
        lookups['field_name__in'] = fields
    if languages is not None:
        lookups['language__in'] = languages
    return lookups


def get_translations_for_save(instance):
    """
    Takes a given instance and returns a list of tuples containing translations
    lookup and cache key for ``Translation`` manager.
    """
    translations = []
    for field in instance.translatable_fields:
        lookup = dict(
            identifier=instance._linguist.identifier,
            object_id=instance.pk,
            language=instance.language,
            field_name=field,
            field_value=getattr(instance, field, ''))
        cache_key = copy.copy(lookup)
        del cache_key['field_value']
        cache_key = get_cache_key(**cache_key)
        translations.append((lookup, cache_key))
    return translations


class ManagerMixin(object):
    """
    Linguist Manager Mixin.
    """

    def save_translations(self):
        instances = self.get_queryset()

    def with_translations(self, fields=None, languages=None):
        """
        Prefetches translations.
        """
        instances = self.get_queryset()
        for instance in instances:
            lookups = get_translation_lookups(instance, fields, languages)
            translations = Translation.objects.filter(**lookups)
            set_instance_cache(instance, translations)


class ModelMixin(object):

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
                           .filter(identifier=self.identifier, object_id=self.pk)
                           .values_list('language', flat=True)
                           .distinct()
                           .order_by('language'))

    def clear_translations_cache(self):
        """
        Clears Linguist cache.
        """
        self._linguist.clear()

    def save_translations(self):
        """
        Saves translations in the database.
        """
        translations = get_translations_for_save(self)
        for lookup, cache_key in translations:
            obj, created = Translation.objects.set_translation(**lookup)
            self._linguist[cache_key] = obj

    def save(self, *args, **kwargs):
        """
        Overwrites model's ``save`` method to save translations after instance
        has been saved (required to retrieve the object ID for ``Translation``
        model).
        """
        super(ModelMixin, self).save(*args, **kwargs)
        self.save_translations()
