# -*- coding: utf-8 -*-
import functools

from django.db import models
from django.db.query import QuerySet

from .models import Translation
from .mixins import LinguistMixin
from .utils.i18n import get_cache_key


def get_value_as_list(value):
    """
    Ensure the given returned value is a list.
    """
    if not isinstance(value, (list, tuple)):
        value = [value]
    return value


def set_instance_cache(instance, translation):
    """
    Sets Linguist cache for the given instance with data from the given translation.
    """
    cache_key = get_cache_key(**dict(
        identifier=instance._linguist.identifier,
        object_id=instance.pk,
        language=translation.language,
        field_name=translation.field_name))
    if cache_key not in instance._linguist:
        instance._linguist[cache_key] = translation
    return instance


def validate_instance(instance):
    """
    Validates the given instance.
    """
    if not isinstance(instance, LinguistMixin):
        raise Exception('%s must be an instance of LinguistMixin' % instance)
    return True


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


class LinguistManager(models.Manager):
    """
    Linguist Manager.
    """

    def with_translations(self, instances, fields=None, languages=None):
        """
        Prefetches translations for the given model instances.
        """
        instances = get_value_as_list(instances)
        for instance in instances:
            validate_instance(instance)
            lookups = get_translation_lookups(instance, fields, languages)
            translations = Translation.objects.filter(**lookups)
            for translation in translations:
                set_instance_cache(instance, translation)
