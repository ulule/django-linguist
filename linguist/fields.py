# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from django.utils.functional import cached_property

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


class Linguist(object):

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance', None)
        self.identifier = kwargs.get('identifier', None)
        self.default_language = kwargs.get('default_language', None)
        self.default_language_field = kwargs.get('default_language_field', None)
        self.fields = kwargs.get('fields', None)
        self.decider = kwargs.get('decider', Translation)

        self.validate_args()

        self.fields = list(self.fields)

        self._language = None

    def validate_args(self):
        """
        Validates arguments.
        """
        from .mixins import ModelMixin

        for arg in ('instance', 'decider', 'identifier', 'fields', 'default_language'):
            if getattr(self, arg) is None:
                raise AttributeError('%s must not be None' % arg)

        if not isinstance(self.instance, (ModelMixin,)):
            raise ImproperlyConfigured('"instance" argument must be a Linguist model')

        if not issubclass(self.decider, (models.Model,)):
            raise ImproperlyConfigured('"decider" argument must be a valid Django model')

    @property
    def active_language(self):
        """
        Returns active language.

        Priorities:

        1. current instance language (if user uses activate_language() method)
        2. default language field (if user defines default language at instance level)
        3. current site language (translation.get_language())
        4. Model._meta.linguist['default_language']
        5. settings.LANGUAGE_CODE

        """
        if self._language is not None:
            return self._language

        if self.default_language_field is not None:
            return self.instance.default_language

        current_language = utils.get_language()

        if current_language in self.supported_languages:
            return current_language

        return self.instance.default_language

    @property
    def language(self):
        return self.active_language

    @language.setter
    def language(self, value):
        self._language = value

    @cached_property
    def supported_languages(self):
        return utils.get_supported_languages()

    @property
    def cached_languages(self):
        langs = []
        for k, v in six.iteritems(self.instance._linguist_translations):
            for lang in v.keys():
                if lang not in langs:
                    langs.append(lang)
        return langs

    @property
    def suffixed_fields(self):
        return utils.get_language_fields(self.fields)

    @property
    def cached_fields(self):
        return [k for k, v in six.iteritems(self.instance._linguist_translations) if v]

    @property
    def cached_suffixed_fields(self):
        return ['%s_%s' % (field, lang)
                for field in self.cached_fields
                for lang in self.supported_languages]

    @property
    def empty_fields(self):
        return list(set(self.fields) - set(self.cached_fields))

    @property
    def empty_suffixed_fields(self):
        return list(set(self.suffixed_fields) - set(self.cached_suffixed_fields))

    @property
    def translations(self):
        """
        Returns translations dictionary.
        """
        return self.instance._linguist_translations

    @property
    def translation_instances(self):
        """
        Returns translation instances.
        """
        return [instance
                for k, v in self.instance._linguist_translations.items()
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
            cached_obj = instance._linguist_translations[field_name][language]
        except KeyError:
            cached_obj = self.get_cached_translation(instance=instance,
                                                     translation=translation,
                                                     language=language,
                                                     field_name=field_name,
                                                     field_value=field_value)
            if not is_new:
                try:
                    obj = self.decider.objects.get(identifier=self.instance.linguist_identifier,
                                                   object_id=self.instance.pk,
                                                   language=language,
                                                   field_name=field_name)
                    cached_obj = CachedTranslation.from_object(obj)
                except self.decider.DoesNotExist:
                    pass

            cached_obj = self.set_cache(cached_obj=cached_obj)

        return cached_obj

    def set_cache(self, instance=None, translation=None, language=None, field_name=None,
                  field_value=None, cached_obj=None):
        """
        Add a new translation into the cache.
        """
        if instance is None:
            instance = self.instance

        if cached_obj is None:
            cached_obj = self.get_cached_translation(instance=instance,
                                                     translation=translation,
                                                     language=language,
                                                     field_name=field_name,
                                                     field_value=field_value)
        try:
            obj = instance._linguist_translations[cached_obj.field_name][cached_obj.language]

            if cached_obj.field_value:
                obj.has_changed = (cached_obj.field_value != obj.field_value)
        except KeyError:
            if cached_obj.field_value is not None:
                instance._linguist_translations[cached_obj.field_name][cached_obj.language] = cached_obj

        return cached_obj


class DefaultLanguageDescriptor(object):
    """
    Default language descriptor.
    """

    def __get__(self, instance, instance_type=None):
        instance_only(instance)

        if instance._linguist.default_language_field is None:
            return instance._linguist.default_language

        default_language = getattr(instance, instance._linguist.default_language_field)

        if callable(default_language):
            return default_language()

        return default_language


class CacheDescriptor(object):
    """
    Cache Descriptor.
    """

    def __init__(self, meta):
        self.identifier = meta.get('identifier', None)
        self.fields = meta.get('fields', None)
        self.default_language = meta.get('default_language', settings.DEFAULT_LANGUAGE)
        self.default_language_field = meta.get('default_language_field', None)
        self.decider = meta.get('decider', Translation)

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        try:
            return getattr(instance, '_linguist_cache')
        except AttributeError:
            linguist = Linguist(instance=instance,
                                identifier=self.identifier,
                                default_language=self.default_language,
                                default_language_field=self.default_language_field,
                                fields=self.fields,
                                decider=self.decider)

            setattr(instance, '_linguist_cache', linguist)
            setattr(instance, '_linguist_translations', defaultdict(dict))

        return instance._linguist_cache


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
        self.column = None

    def __get__(self, instance, instance_type=None):
        instance_only(instance)

        obj = instance._linguist.get_cache(instance=instance,
                                           language=self.language,
                                           field_name=self.translated_field.name)
        return obj.field_value or ''

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


class TranslationField(object):
    """
    Proxy of original field.
    """

    def __init__(self, translated_field, language, *args, **kwargs):
        self.__dict__.update(translated_field.__dict__)

        self.translated_field = translated_field
        self.language = language

        # Suffix field with '_fr', '_en', etc.
        self.attname = utils.build_localized_field_name(self.translated_field.name, language)
        self.name = self.attname
        self.verbose_name = utils.build_localized_verbose_name(translated_field.verbose_name, language)

        # No concrete field Django < 1.8
        self.column = None

        # No concret field Django >= 1.8
        self.concrete = False

    def contribute_to_class(self, cls, name):
        self.model = cls
        self.name = name
        setattr(cls, self.name, TranslationDescriptor(self, self.translated_field, self.language))
        cls._meta.add_field(self)
        cls._meta.virtual_fields.append(self)

    def db_type(self, connection):
        """
        Returning None will cause Django to exclude this field from the concrete
        field list (``_meta.concrete_fields``) resulting in the fact that syncdb
        will skip this field when creating tables in PostgreSQL.
        """
        return None

    def deconstruct(self):
        name, path, args, kwargs = self.translated_field.deconstruct()
        if self.null is True:
            kwargs.update({'null': True})
        return six.text_type(self.name), path, args, kwargs
