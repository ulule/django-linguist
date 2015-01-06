# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from . import settings
from . import utils

from collections import defaultdict

from django.core.exceptions import ImproperlyConfigured
from django.db import models

from .cache import CachedTranslation
from .models import Translation

SUPPORTED_FIELDS = (
    models.fields.CharField,
    models.fields.TextField,
)


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

    def __init__(self, field, translated_field, language):
        self.field = field
        self.translated_field = translated_field
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
        obj = instance._linguist.get_cache(instance=instance,
                                           language=self.language,
                                           field_name=self.translated_field.name)
        return obj.field_value or None

    def __set__(self, instance, value):
        instance_only(instance)
        if value:
            instance._linguist.set_cache(instance=instance,
                                         language=self.language,
                                         field_name=self.translated_field.name,
                                         field_value=value)

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
        self['default_language'] = self._translation_class.default_language or settings.DEFAULT_LANGUAGE
        self['language'] = self['default_language']
        self['translations'] = defaultdict(dict)

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
        """
        Returns translations dictionary.
        """
        return self['translations']

    @property
    def translation_instances(self):
        """
        Returns translation instances.
        """
        return [instance
                for k, v in self.translations.items()
                for instance in v.values()]

    @property
    def translations_count(self):
        """
        Returns translations count.
        """
        return len(self.translation_instances)

    def get_cached_translation(self, instance, translation=None, language=None,
                               field_name=None, field_value=None):
        """
        Returns CachedTranslation instance.
        """
        if translation is None:
            if not (language and field_name):
                raise Exception("You must set language and field name")

        if translation is not None:
            language = translation.language
            field_name = translation.field_name
            field_value = translation.field_value

        return CachedTranslation(instance=instance,
                                 language=language,
                                 field_name=field_name,
                                 field_value=field_value)

    def get_cache(self, instance, translation=None, language=None, field_name=None,
                  field_value=None):
        """
        Returns translation from cache.
        """
        is_new = bool(instance.pk is None)

        try:
            cached_obj = self.translations[field_name][language]
        except KeyError:
            cached_obj = self.get_cached_translation(instance=instance,
                                                     translation=translation,
                                                     language=language,
                                                     field_name=field_name,
                                                     field_value=field_value)
            if not is_new:
                try:
                    obj = Translation.objects.get(**cached_obj.lookup_get)
                    cached_obj = cached_obj.from_object(obj)
                except Translation.DoesNotExist:
                    pass

            self.set_cache(cached_obj=cached_obj)

        return cached_obj

    def set_cache(self, instance=None, translation=None, language=None, field_name=None,
                  field_value=None, cached_obj=None):
        """
        Add a new translation into the cache.
        """
        if cached_obj is None:
            cached_obj = self.get_cached_translation(instance=instance,
                                                     translation=translation,
                                                     language=language,
                                                     field_name=field_name,
                                                     field_value=field_value)

        try:
            cached_obj = self.translations[cached_obj.field_name][cached_obj.language]
        except KeyError:
            if cached_obj.field_value:
                self.translations[cached_obj.field_name][cached_obj.language] = cached_obj
        return cached_obj


class TranslationField(object):
    """
    Proxy of original field.
    """

    def __init__(self, translated_field, language, *args, **kwargs):
        self.__dict__.update(translated_field.__dict__)
        self.translated_field = translated_field
        self.language = language

        # All translations are optional
        if not isinstance(self, models.fields.BooleanField):
            self.null = True
        self.blank = True

        # Suffix field with '_fr', '_en', etc.
        self.attname = utils.build_localized_field_name(self.translated_field.name, language)
        self.name = self.attname
        self.verbose_name = utils.build_localized_verbose_name(translated_field.verbose_name, language)

        # No concrete field
        self.column = None

    def contribute_to_class(self, cls, name):
        setattr(cls, self.name, TranslationDescriptor(self, self.translated_field, self.language))
        cls._meta.add_field(self)
        cls._meta.virtual_fields.append(self)


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


def field_factory(base_class):
    class TranslationFieldField(TranslationField, base_class):
        pass
    TranslationFieldField.__name__ = b'Translation%s' % base_class.__name__
    return TranslationFieldField


def create_translation_field(translated_field, language):
    """
    Takes the original field, a given language and return a Field class for model.
    """
    cls_name = translated_field.__class__.__name__

    if not isinstance(translated_field, SUPPORTED_FIELDS):
        raise ImproperlyConfigured('%s is not supported by Linguist.' % cls_name)

    translation_class = field_factory(translated_field.__class__)

    return translation_class(translated_field=translated_field, language=language)


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
            localized_field_name = utils.build_localized_field_name(field.name, language_code)
            translation_field = create_translation_field(field, language_code)
            if hasattr(model, localized_field_name):
                raise ValueError(
                    "Error adding translation field. Model '%s' already contains a field named"
                    "'%s'." % (model._meta.object_name, localized_field_name))
            translation_field.contribute_to_class(model, localized_field_name)


def contribute_to_model(translation_class):
    """
    Add linguist fields and properties to translation class model.
    """
    add_cache_property(translation_class)
    add_language_fields(translation_class)
    add_translatable_fields(translation_class)
