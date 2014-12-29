# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from . import settings
from . import utils

from .cache import CachedTranslation
from .models import Translation


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
        self.attname = utils.build_localized_field_name(self.field.name, language)
        self.name = self.attname
        self.verbose_name = utils.build_localized_verbose_name(field.verbose_name, language)
        self.null = True
        self.blank = True
        self.column = None
        self.editable = True

    def __get__(self, instance, instance_type=None):
        instance_only(instance)
        return self.get_translated_value(instance, self.language, self.field.name)

    def __set__(self, instance, value):
        instance_only(instance)
        if value:
            self.cache_translation(instance, self.language, self.field.name, value)

    def db_type(self, connection):
        """
        Returning None will cause Django to exclude this field from the concrete
        field list (``_meta.concrete_fields``) resulting in the fact that syncdb
        will skip this field when creating tables in PostgreSQL.
        """
        return None

    def cache_translation(self, instance, language, field_name, value):
        """
        Caches a translation.
        """
        is_new = bool(instance.pk is None)

        cache_key = utils.make_cache_key(**{
            'instance': instance,
            'language': language,
            'field_name': field_name,
        })

        if cache_key in instance._linguist.translations:
            instance._linguist.translations[cache_key].field_value = value
            return

        cached_obj = CachedTranslation(**{
            'instance': instance,
            'language': language,
            'field_name': field_name,
            'field_value': value,
        })

        obj = None

        if not is_new:
            try:
                obj = Translation.objects.get(**cached_obj.attrs)
            except Translation.DoesNotExist:
                pass

        if obj is not None:
            cached_obj = cached_obj.from_object(obj)

        instance._linguist.translations[cache_key] = cached_obj

    def get_translated_value(self, instance, language, field_name):
        """
        Takes a language and a field name and returns the cached
        Translation instance if found, otherwise retrieves it from the database
        and cached it.
        """
        is_new = bool(instance.pk is None)

        cache_key = utils.make_cache_key(**{
            'instance': instance,
            'language': language,
            'field_name': field_name
        })

        if cache_key in instance._linguist.translations:
            return instance._linguist.translations[cache_key].field_value

        cached_obj = CachedTranslation(**{
            'instance': instance,
            'language': language,
            'field_name': field_name,
        })

        obj = None

        if not is_new:
            try:
                obj = Translation.objects.get(**cached_obj.attrs)
            except Translation.DoesNotExist:
                pass

        if obj is not None:
            cached_obj = cached_obj.from_object(obj)
            instance._linguist[cache_key] = cached_obj
            return obj.field_value

        return None


class CacheDescriptor(dict):
    """
    Linguist Cache Descriptor.
    """

    def __init__(self, translation_class):
        self._translation_class = translation_class
        self['identifier'] = self._translation_class.identifier
        self['fields'] = self._translation_class.fields
        self['default_language'] = self._translation_class.default_language or settings.DEFAULT_LANGUAGE
        self['language'] = self['default_language']
        self['translations'] = {}

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

    @property
    def translations(self):
        return self['translations']


def default_value_getter(field):
    """
    When accessing to the name of the field itself, the value
    in the current language will be returned. Unless it's set,
    the value in the default language will be returned.
    """
    def default_value_func_getter(self):
        language = self.language or self.default_language
        localized_field = utils.build_localized_field_name(field, language)
        return getattr(self, localized_field)
    return default_value_func_getter


def default_value_setter(field):
    """
    When setting to the name of the field itself, the value
    in the current language will be set.
    """
    def default_value_func_setter(self, value):
        language = self.language or self.default_language
        localized_field = utils.build_localized_field_name(field, language)
        setattr(self, localized_field, value)
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
            localized_field_name = utils.build_localized_field_name(field.name, language_code)
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
