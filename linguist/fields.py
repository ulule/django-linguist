# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict

from django.utils import six

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


class CacheDescriptor(dict):
    """
    Linguist Cache Descriptor.
    """

    def __init__(self, meta):

        self['identifier'] = meta['identifier']
        self['fields'] = meta['fields']

        default_language = settings.DEFAULT_LANGUAGE

        if 'default_language' in meta:
            default_language = meta['default_language']

        self['default_language'] = default_language
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
    def supported_languages(self):
        return [code.replace('-', '_') for code, name in settings.SUPPORTED_LANGUAGES]

    @property
    def cached_languages(self):
        langs = []
        for k, v in six.iteritems(self.translations):
            for lang in v.keys():
                if lang not in langs:
                    langs.append(lang)
        return langs

    @property
    def fields(self):
        """
        Returns translatable fields (from related translation class).
        Read-only.
        """
        return list(self['fields'])

    @property
    def suffixed_fields(self):
        return ['%s_%s' % (field, lang)
                for field in self.fields
                for lang in self.supported_languages]

    @property
    def cached_fields(self):
        return [k for k, v in six.iteritems(self.translations) if v]

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

        cached_obj = self.get_cached_translation(instance=instance,
                                                 translation=translation,
                                                 language=language,
                                                 field_name=field_name,
                                                 field_value=field_value)

        try:
            cached_obj = self.translations[cached_obj.field_name][cached_obj.language]
        except KeyError:
            if not is_new:
                try:
                    obj = Translation.objects.get(**cached_obj.lookup)
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
            obj = self.translations[cached_obj.field_name][cached_obj.language]
            if cached_obj.field_value:
                obj.has_changed = (cached_obj.field_value != obj.field_value)
        except KeyError:
            if cached_obj.field_value is not None:
                self.translations[cached_obj.field_name][cached_obj.language] = cached_obj

        return cached_obj


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

        # No concrete field
        self.column = None

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
