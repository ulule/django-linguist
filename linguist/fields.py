# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy

from django.core.exceptions import ImproperlyConfigured
from django.db.models import fields

from . import settings
from .models import Translation
from .utils import (get_cache_key,
                    get_language,
                    build_localized_field_name,
                    build_localized_verbose_name)


SUPPORTED_FIELDS = (
    fields.CharField,
    fields.TextField,
)


class TranslatedField(object):
    """
    Translated field.
    """

    def __init__(self, field):
        self.field = field

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError('Can only be accessed via instance')
        field_name = build_localized_field_name(self.field.name, get_language())
        setattr(instance, field_name, value)

    def __get__(self, instance, instance_type=None):
        if instance is None:
            raise AttributeError('Can only be accessed via instance')
        field_name = build_localized_field_name(self.field.name, get_language())
        return getattr(instance, field_name, None)


class TranslationField(object):
    """
    Translation field.
    """

    def __init__(self, identifier, field, language, *args, **kwargs):
        self.identifier = identifier
        self.field = field
        self.language = language
        self.attname = build_localized_field_name(self.field.name, language)
        self.name = self.attname
        self.verbose_name = build_localized_verbose_name(field.verbose_name, language)
        self.null = True
        self.blank = True

    def __get__(self, instance, instance_type=None):
        if instance is None:
            raise AttributeError('Can only be accessed via instance')

        kwargs = dict(
            identifier=self.identifier,
            object_id=instance.pk,
            language=self.language,
            field_name=self.field.name)

        cache_key = get_cache_key(**kwargs)

        if not hasattr(instance, '_linguist'):
            instance._linguist = {}

        if cache_key in instance._linguist:
            return instance._linguist[cache_key].field_value

        translation = Translation.objects.get_translation(**kwargs)
        if translation:
            instance._linguist[cache_key] = translation
            return translation.field_value

        return getattr(instance, self.field.name)

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError('Can only be accessed via instance')

        kwargs = dict(
            identifier=self.identifier,
            object_id=instance.pk,
            language=self.language,
            field_name=self.field.name,
            field_value=value)

        cache_kwargs = copy.copy(kwargs)
        del cache_kwargs['field_value']
        cache_key = get_cache_key(**cache_kwargs)

        if not hasattr(instance, '_linguist'):
            instance._linguist = {}

        obj, created = Translation.objects.set_translation(**kwargs)
        instance._linguist[cache_key] = obj


def create_translation_field(identifier, model, field_name, language):
    """
    Returns a ``TranslationField`` based on a ``field_name`` and a ``language``.
    """
    field = model._meta.get_field(field_name)
    cls_name = field.__class__.__name__
    if not isinstance(field, SUPPORTED_FIELDS):
        raise ImproperlyConfigured('%s is not supported by Linguist.' % cls_name)
    return TranslationField(
        identifier=identifier,
        field=field,
        language=language)


def add_translation_fields(translation_class):
    """
    Patches original model to provide fields for each language.
    """
    model = translation_class.model
    fields = translation_class.fields
    for field_name in fields:
        for language, name in settings.SUPPORTED_LANGUAGES:
            translation_field = create_translation_field(
                identifier=translation_class.identifier,
                model=model,
                field_name=field_name,
                language=language)
            localized_field_name = build_localized_field_name(field_name, language)
            if hasattr(model, localized_field_name):
                raise ValueError(
                    "Error adding translation field. Model '%s' already contains a field named"
                    "'%s'." % (model._meta.object_name, localized_field_name))
            model.add_to_class(localized_field_name, translation_field)
