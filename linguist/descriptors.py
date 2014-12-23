# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy

from django.core.exceptions import ImproperlyConfigured
from django.db.models import fields

from . import settings
from .models import Translation
from .utils.i18n import (get_cache_key,
                         get_language,
                         get_fallback_language,
                         build_localized_field_name,
                         build_localized_verbose_name)


def instance_only(instance):
    """
    Ensures instance is not None for ``__get__`` and ``__set__`` methods.
    """
    if instance is None:
        raise AttributeError('Can only be accessed via instance')


class TranslationDescriptor(object):
    """
    Translation Field Descriptor.
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
        instance_only(instance)
        return instance._linguist.get_translated_value(
            instance,
            self.language,
            self.field.name)

    def __set__(self, instance, value):
        instance_only(instance)
        instance._linguist.cache_translation(
            instance,
            self.language,
            self.field.name,
            value)

    def db_type(self, connection):
        """
        Returning None will cause Django to exclude this field from the concrete
        field list (``_meta.concrete_fields``) resulting in the fact that syncdb
        will skip this field when creating tables in PostgreSQL.
        """
        return None


class CacheDescriptor(dict):
    """
    Linguist Cache Descriptor.
    """

    def __init__(self, translation_class):
        self._translation_class = translation_class
        self['identifier'] = self._translation_class.identifier
        self['fields'] = self._translation_class.fields
        self['default_language'] = self._translation_class.default_language
        self['language'] = get_language()

    @property
    def identifier(self):
        """
        Returns model identifier (from related translation class).
        Read-only.
        """
        return self['identifier']

    @property
    def language(self):
        """
        Returns current language.
        """
        return self['language']

    @language.setter
    def language(self, value):
        """
        Sets current language.
        """
        self['language'] = value

    @property
    def default_language(self):
        """
        Returns default language.
        """
        return self['default_language']

    @default_language.setter
    def default_language(self, value):
        """
        Sets default language.
        """
        self['default_language'] = value

    @property
    def fields(self):
        """
        Returns translatable fields (from related translation class).
        Read-only.
        """
        return self['fields']

    @property
    def translation_class(self):
        """
        Returns related translation class.
        Read-only.
        """
        return self._translation_class

    def cache_translation(self, instance, language, field_name, value):
        """
        Caches the translation.
        """
        attrs = dict(
            identifier=instance.linguist_identifier,
            object_id=instance.pk,
            language=language,
            field_name=field_name)

        cache_key = get_cache_key(**attrs)

        # First, try to fetch from the cache
        cached = self[cache_key] if cache_key in self else None

        # Cache exists? Update the value!
        if cached is not None:
            self[cache_key]['field_value'] = value
        else:
            # No cache? Try to fetch it from database
            obj = None
            try:
                obj = Translation.objects.get(**attrs)
            except instance._meta.model.DoesNotExist:
                pass
            # Object exists? Assign pk!
            # Object doesn't exist? Set pk to None, we'll create object later at save
            attrs['pk'] = obj.pk if obj is not None else None
            attrs['field_value'] = value
            self[cache_key] = attrs

    def get_translated_value(self, instance, language, field_name):
        """
        Takes an instance, a language and a field name and returns the cached
        Translation instance if found, otherwise retrieves it from the database
        and cached it.
        """
        attrs = dict(
            identifier=instance._linguist_identifier,
            object_id=instance.pk,
            language=language,
            field_name=field_name)

        cache_key = get_cache_key(**attrs)

        # First, try the fetch the value from the cache
        if cache_key in self:
            return self[cache_key].field_value

        # Value is not cached? Try to fetch it from database
        obj = None
        try:
            obj = Translation.objects.get(**attrs)
        except instance._meta.model.DoesNotExist:
            pass

        # A translation object exists! Let's return its value
        if obj is not None:
            attrs['pk'] = obj.pk if obj is not None else None
            attrs['field_value'] = obj.field_value
            self[cache_key] = attrs
            return obj.field_value

        # No cache, no object in database... so return None
        return None


def default_value_getter(field):
    """
    When accessing to the name of the field itself, the value
    in the current language will be returned. Unless it's set,
    the value in the default language will be returned.
    """
    def default_value_func_getter(self):
        attname = lambda x: build_localized_field_name(field, x)
        language = None
        current_language = get_language()
        if getattr(self, attname(current_language), None):
            language = current_language
        elif getattr(self, attname(current_language[:2]), None):
            language = current_language[:2]
        else:
            try:
                default_language = getattr(self, getattr(self._meta, 'default_language_field'))
                if not default_language:
                    raise
            except:
                default_language = get_fallback_language()
            if getattr(self, attname(default_language), None):
                language = default_language
            else:
                language = default_language[:2]
        if language:
            return getattr(self, attname(language))
    return default_value_func_getter


def default_value_setter(field):
    """
    When setting to the name of the field itself, the value
    in the current language will be set.
    """
    def default_value_func_setter(self, value):
        attname = lambda x: build_localized_field_name(field, x)
        language = None
        current_language = get_language()
        if hasattr(self, attname(current_language)):
            language = current_language
        elif hasattr(self, attname(current_language[:2])):
            language = current_language[:2]
        else:
            try:
                default_language = getattr(self, getattr(self._meta, 'default_language_field'))
                if not default_language:
                    raise
            except:
                default_language = current_language
            if hasattr(self, attname(default_language)):
                language = default_language
            elif hasattr(self, attname(default_language[:2])):
                language = default_language[:2]
        if language:
            setattr(self, attname(language), value)
    return default_value_func_setter


def add_cache_property(translation_class):
    """
    Adds the linguist cache property to the translation class model.
    """
    translation_class.model.add_to_class('_linguist', CacheDescriptor(translation_class))


def add_translatable_fields(translation_class):
    """
    Adds translatable fields of translation class model.
    """
    model = translation_class.model
    fields = translation_class.fields
    for field_name in fields:
        field = model._meta.get_field(field_name)
        setattr(model, field_name, property(default_value_getter(field_name),
                                            default_value_setter(field_name)))

def add_language_fields(translation_class):
    """
    Adds language fields for each translatable field of translation class model.
    """
    model = translation_class.model
    fields = translation_class.fields
    for field_name in fields:
        field = model._meta.get_field(field_name)
        for language_code, language_name in settings.SUPPORTED_LANGUAGES:
            translation_field = TranslationDescriptor(field, language_code)
            localized_field_name = build_localized_field_name(field.name, language_code)
            if hasattr(model, localized_field_name):
                raise ValueError(
                    "Error adding translation field. Model '%s' already contains a field named"
                    "'%s'." % (model._meta.object_name, localized_field_name))
            model.add_to_class(localized_field_name, translation_field)
            model._meta.fields.append(translation_field)


def contribute_to_model(translation_class):
    """
    Add linguist fields and properties to translation class model.
    """
    add_cache_property(translation_class)
    add_language_fields(translation_class)
    add_translatable_fields(translation_class)
