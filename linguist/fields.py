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

    def getter_cache(self, instance, field_name, original_field_name, language):
        if instance is None:
            raise AttributeError('Can only be accessed via instance')

        kwargs = dict(
            identifier=instance._linguist.identifier,
            object_id=instance.pk,
            language=language,
            field_name=original_field_name)

        cache_key = get_cache_key(**kwargs)
        if cache_key in instance._linguist:
            return instance._linguist[cache_key].field_value

        translation = Translation.objects.get_translation(**kwargs)

        if translation:
            instance._linguist[cache_key] = translation
            return translation.field_value

    def setter_cache(self, instance, field_name, original_field_name, language, value):
        if instance is None:
            raise AttributeError('Can only be accessed via instance')

        if not instance.pk:
            return

        kwargs = dict(
            identifier=instance._linguist.identifier,
            object_id=instance.pk,
            language=language,
            field_name=original_field_name,
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
        return self.getter_cache(instance=instance,
                                 field_name=self.name,
                                 original_field_name=self.field.name,
                                 language=self.language)

    def __set__(self, instance, value):
        self.setter_cache(instance=instance,
                          field_name=self.name,
                          original_field_name=self.field.name,
                          language=self.language,
                          value=value)


class CacheDescriptor(dict):

    def __init__(self, identifier):
        self._identifier = identifier
        self['identifier'] = self._identifier
        self['language'] = get_language()

    @property
    def language(self):
        return self['language']

    @language.setter
    def language(self, value):
        self['language'] = value

    @property
    def identifier(self):
        return self['identifier']

    @identifier.setter
    def identifier(self, value):
        self['identifier'] = value


def contribute_to_model(translation_class):
    """
    Temporarly adds translation class to model to pass it to metaclass.
    """
    model.add_to_class('linguist_translation_class', translation_class)
