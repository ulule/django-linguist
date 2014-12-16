# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy

from django.core.exceptions import ImproperlyConfigured
from django.db.models import fields

from . import settings
from .models import Translation
from .utils.i18n import (get_cache_key,
                         get_language,
                         build_localized_field_name,
                         build_localized_verbose_name)


SUPPORTED_FIELDS = (
    fields.CharField,
    fields.TextField,
)


class TranslationFieldMixin(object):
    """
    Common logic for translated and translation fields.
    """

    def getter_cache(self, instance, field_name, language):
        if instance is None:
            raise AttributeError('Can only be accessed via instance')

        kwargs = dict(
            identifier=instance._linguist.identifier,
            object_id=instance.pk,
            language=language,
            field_name=field_name)

        cache_key = get_cache_key(**kwargs)
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
            identifier=instance._linguist.identifier,
            object_id=instance.pk,
            language=language,
            field_name=field_name,
            field_value=value)

        cache_kwargs = copy.copy(kwargs)
        del cache_kwargs['field_value']
        cache_key = get_cache_key(**cache_kwargs)

        obj, created = Translation.objects.set_translation(**kwargs)
        instance._linguist[cache_key] = obj

    def db_type(self, connection):
        """
        Returning None will cause Django to exclude this field from the concrete
        field list (``_meta.concrete_fields``) resulting in the fact that syncdb
        will skip this field when creating tables in PostgreSQL.
        """
        return None


class TranslatedField(TranslationFieldMixin):
    """
    Translated field.
    """

    def __init__(self, field):
        self.field = field
        self.attname = self.field.name
        self.name = self.attname
        self.column = None
        self.editable = True

    def __get__(self, instance, instance_type=None):
        field_name = build_localized_field_name(self.field.name, instance.language)
        return self.getter_cache(instance, field_name, instance.language)

    def __set__(self, instance, value):
        field_name = build_localized_field_name(self.field.name, instance.language)
        self.setter_cache(instance, field_name, instance.language, value)


class TranslationField(TranslationFieldMixin):
    """
    Translation field.
    """

    def __init__(self, field, language):
        self.field = field
        self.language = language
        self.attname = build_localized_field_name(self.field.name, language)
        self.name = self.attname
        self.verbose_name = build_localized_verbose_name(field.verbose_name, language)
        self.null = True
        self.blank = True
        self.column = None
        self.editable = True

    def __get__(self, instance, instance_type=None):
        return self.getter_cache(instance, self.name, self.language)

    def __set__(self, instance, value):
        self.setter_cache(instance, self.name, self.language, value)


class CacheDescriptor(dict):

    def __init__(self, identifier):
        self._identifier = identifier
        self['identifier'] = self._identifier

    @property
    def language(self):
        return self['language'] if 'language' in self else get_language()

    @language.setter
    def language(self, value):
        self['language'] = value

    @property
    def identifier(self):
        return self['identifier'] if 'identifier' in self else self._identifier

    @identifier.setter
    def identifier(self, value):
        self['identifier'] = value


def add_cache_property(model, identifier):
    """
    Adds cache property to model.
    """
    model.add_to_class('_linguist', CacheDescriptor(identifier))


def add_translated_field(model, field_name):
    """
    Replaces translated field with `TranslatedField` descriptor.
    """
    if field_name in model._meta.get_all_field_names():
        field = model._meta.get_field(field_name)
        setattr(model, field_name, TranslatedField(field))


def add_translation_fields(model, field_name):
    """
    Adds translation fields to given model.
    """
    field = model._meta.get_field(field_name)
    field_names = [f.name for f in model._meta.fields]
    cls_name = field.__class__.__name__

    if not isinstance(field, SUPPORTED_FIELDS):
        raise ImproperlyConfigured('%s is not supported by Linguist.' % cls_name)

    for language_code, language_name in settings.SUPPORTED_LANGUAGES:
        translation_field = TranslationField(field, language_code)
        localized_field_name = build_localized_field_name(field_name, language_code)
        if hasattr(model, localized_field_name):
            raise ValueError(
                "Error adding translation field. Model '%s' already contains a field named"
                "'%s'." % (model._meta.object_name, localized_field_name))
        if localized_field_name not in field_names:
            model.add_to_class(localized_field_name, translation_field)
            model._meta.fields.append(translation_field)


def contribute_to_model(translation_class):
    """
    Adds fields and properties to model.
    """
    identifier = translation_class.identifier
    model = translation_class.model
    fields = translation_class.fields

    add_cache_property(model, identifier)

    for field_name in fields:
        add_translated_field(model, field_name)
        add_translation_fields(model, field_name)
