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


class TranslationFieldMixin(object):

    def getter_cache(self, instance, field_name, language):
        if instance is None:
            raise AttributeError('Can only be accessed via instance')
        kwargs = dict(
            identifier=self.identifier,
            object_id=instance.pk,
            language=language,
            field_name=field_name)
        cache_key = get_cache_key(**kwargs)
        if not hasattr(instance, '_linguist'):
            instance._linguist = {}
        if cache_key in instance._linguist:
            return instance._linguist[cache_key].field_value
        translation = Translation.objects.get_translation(**kwargs)
        if translation:
            instance._linguist[cache_key] = translation
            return translation.field_value

    def setter_cache(self, instance, field_name, language, value):
        if instance is None:
            raise AttributeError('Can only be accessed via instance')
        kwargs = dict(
            identifier=self.identifier,
            object_id=instance.pk,
            language=language,
            field_name=field_name,
            field_value=value)
        cache_kwargs = copy.copy(kwargs)
        del cache_kwargs['field_value']
        cache_key = get_cache_key(**cache_kwargs)
        if not hasattr(instance, '_linguist'):
            instance._linguist = {}
        obj, created = Translation.objects.set_translation(**kwargs)
        instance._linguist[cache_key] = obj


class TranslatedField(TranslationFieldMixin):
    """
    Translated field.
    """

    def __init__(self, identifier, field):
        self.identifier = identifier
        self.field = field

    def __get__(self, instance, instance_type=None):
        language = instance.get_current_language()
        field_name = build_localized_field_name(self.field.name, language)
        return self.getter_cache(instance, field_name, language)

    def __set__(self, instance, value):
        language = instance.get_current_language()
        field_name = build_localized_field_name(self.field.name, language)
        self.setter_cache(instance, field_name, language, value)


class TranslationField(TranslationFieldMixin):
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
        return self.getter_cache(instance, self.name, self.language)

    def __set__(self, instance, value):
        self.setter_cache(instance, self.name, self.language, value)


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


def add_translated_field(model, identifier, field_name):
    """
    Replaces translated field with `TranslatedField` descriptor.
    """
    if field_name not in model._meta.get_all_field_names():
        print('NOT FIELD NAME')
        return
    if not hasattr(model._meta, 'linguist_translated_fields'):
        model._meta.linguist_translated_fields = {}
    field = model._meta.get_field(field_name)
    model._meta.linguist_translated_fields[field_name] = field
    setattr(model, field_name, TranslatedField(identifier=identifier, field=field))


def add_translation_fields(translation_class):
    """
    Patches original model to provide fields for each language.
    """
    identifier = translation_class.identifier
    model = translation_class.model
    fields = translation_class.fields
    for field_name in fields:
        add_translated_field(model=model, identifier=identifier, field_name=field_name)
        for language, name in settings.SUPPORTED_LANGUAGES:
            translation_field = create_translation_field(
                identifier=identifier,
                model=model,
                field_name=field_name,
                language=language)
            localized_field_name = build_localized_field_name(field_name, language)
            if hasattr(model, localized_field_name):
                raise ValueError(
                    "Error adding translation field. Model '%s' already contains a field named"
                    "'%s'." % (model._meta.object_name, localized_field_name))
            model.add_to_class(localized_field_name, translation_field)
