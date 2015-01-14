# -*- coding: utf-8 -*-
from contextlib import contextmanager
import copy
import itertools

from collections import defaultdict

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.fields import NOT_PROVIDED
from django.utils.translation import string_concat
from django.utils import six

from . import settings
from . import utils

LANGUAGE_CODE, LANGUAGE_NAME = 0, 1


def set_instance_cache(instance, translations):
    """
    Sets Linguist cache for the given instance.
    """
    instance.clear_translations_cache()
    for translation in translations:
        instance._linguist.set_cache(instance=instance, translation=translation)
    return instance


def validate_meta(meta):
    """
    Validates Linguist Meta attribute.
    """
    if not isinstance(meta, (dict,)):
        raise TypeError('Model Meta "linguist" must be a dict')

    required_keys = ('identifier', 'fields')

    for key in required_keys:
        if key not in meta:
            raise KeyError('Model Meta "linguist" dict requires %s to be defined', key)

    if not isinstance(meta['fields'], (list, tuple)):
        raise ImproperlyConfigured("Linguist Meta's fields attribute must be a list or tuple")


class ModelMeta(models.base.ModelBase):

    def __new__(cls, name, bases, attrs):

        from .fields import default_value_getter, default_value_setter
        from .fields import create_translation_field
        from .fields import CacheDescriptor
        from .base import ModelTranslationBase

        meta = None
        default_language = utils.get_fallback_language()
        default_language_field = None

        if 'Meta' in attrs and hasattr(attrs['Meta'], 'linguist'):
            validate_meta(attrs['Meta'].linguist)
            meta = attrs['Meta'].linguist
            delattr(attrs['Meta'], 'linguist')
        else:
            return super(ModelMeta, cls).__new__(cls, name, bases, attrs)

        all_fields = dict(
            (attr_name, attr)
            for attr_name, attr in attrs.iteritems()
            if isinstance(attr, models.fields.Field))

        abstract_model_bases = [
            base
            for base in bases
            if hasattr(base, '_meta') and base._meta.abstract
        ]

        for base in abstract_model_bases:
            all_fields.update(dict((field.name, field) for field in base._meta.fields))

        original_fields = {}

        for field in meta['fields']:

            if not field in all_fields:
                raise ImproperlyConfigured(
                    "There is no field %(field)s in model %(name)s, "\
                    "as specified in Meta's translate attribute" % \
                    dict(field=field, name=name))

            original_fields[field] = all_fields[field]

            if field in attrs:
                del attrs[field]

        new_class = super(ModelMeta, cls).__new__(cls, name, bases, attrs)

        for field_name, field in six.iteritems(original_fields):

            field.name = field_name
            field.model = new_class

            for lang in settings.SUPPORTED_LANGUAGES:

                lang_code = lang[LANGUAGE_CODE]
                lang_attr = create_translation_field(field, lang_code)
                lang_attr_name = utils.get_real_field_name(field_name, lang_code)

                if lang_code != default_language:
                    if not lang_attr.null and lang_attr.default is NOT_PROVIDED:
                        lang_attr.null = True
                    if not lang_attr.blank:
                        lang_attr.blank = True

                if lang_attr.verbose_name:
                    lang_attr.verbose_name = string_concat(lang_attr.verbose_name, u' (%s)' % lang_code)

                lang_attr.contribute_to_class(new_class, lang_attr_name)

            setattr(new_class,
                    field_name,
                    property(default_value_getter(field), default_value_setter(field)))

        new_class._linguist = CacheDescriptor(new_class, meta)
        new_class._meta.linguist = meta

        return new_class


class ManagerMixin(object):
    """
    Linguist Manager Mixin.
    """

    def with_translations(self, **kwargs):
        """
        Prefetches translations.

        Takes three optional keyword arguments:

        * ``field_names``: ``field_name`` values for SELECT IN
        * ``languages``: ``language`` values for SELECT IN
        * ``chunks_length``: fetches IDs by chunk

        """
        from .models import Translation

        qs = self.get_queryset()

        chunks_length = kwargs.get('chunks_length', None)

        lookup = dict(identifier=self.model._linguist.identifier)

        for kwarg in ('field_names', 'languages'):
            value = kwargs.get(kwarg, None)
            if value is not None:
                if not isinstance(value, (list, tuple)):
                    value = [value]

                lookup['%s__in' % kwarg[:-1]] = value

        if chunks_length is not None:
            translations_qs = []

            for ids in utils.chunks(qs.values_list('id', flat=True), chunks_length):
                ids_lookup = copy.copy(lookup)
                ids_lookup['object_id__in'] = ids
                translations_qs.append(Translation.objects.filter(**ids_lookup))

            translations = itertools.chain.from_iterable(translations_qs)
        else:
            lookup['object_id__in'] = [obj.pk for obj in qs]
            translations = Translation.objects.filter(**lookup)

        grouped_translations = defaultdict(list)

        for obj in translations:
            grouped_translations[obj.object_id].append(obj)

        for instance in qs:
            set_instance_cache(instance, grouped_translations[instance.pk])


class ModelMixin(object):

    __metaclass__ = ModelMeta

    @property
    def linguist_identifier(self):
        """
        Returns Linguist's identifier for this model.
        """
        return self._linguist.identifier

    @property
    def default_language(self):
        """
        Returns model default language.
        """
        return self._linguist.default_language

    @default_language.setter
    def default_language(self, value):
        """
        Sets model default language.
        """
        self._linguist.language = value
        self._linguist.default_language = value

    @property
    def translatable_fields(self):
        """
        Returns Linguist's translation class fields (translatable fields).
        """
        return self._linguist.fields

    @property
    def available_languages(self):
        """
        Returns available languages.
        """
        from .models import Translation

        return (Translation.objects
                .filter(identifier=self.linguist_identifier, object_id=self.pk)
                .values_list('language', flat=True)
                .distinct()
                .order_by('language'))

    @property
    def cached_translations_count(self):
        """
        Returns cached translations count.
        """
        return self._linguist.translations_count

    def clear_translations_cache(self):
        """
        Clears Linguist cache.
        """
        self._linguist.translations.clear()

    def get_translations(self, language=None):
        """
        Returns available (saved) translations for this instance.
        """
        from .models import Translation

        if not self.pk:
            return Translation.objects.none()

        return Translation.objects.get_translations(obj=self, language=language)

    def delete_translations(self, language=None):
        """
        Deletes related translations.
        """
        from .models import Translation

        return Translation.objects.delete_translations(obj=self, language=language)

    def activate_language(self, language):
        """
        Context manager to override the instance language.
        """
        self._linguist.language = language

    @contextmanager
    def override_language(self, language):
        """
        Context manager to override the instance language.
        """
        previous_language = self._linguist.language
        self._linguist.language = language
        yield
        self._linguist.language = previous_language

    def save(self, *args, **kwargs):
        """
        Overwrites model's ``save`` method to save translations after instance
        has been saved (required to retrieve the object ID for ``Translation``
        model).
        """
        from .models import Translation

        super(ModelMixin, self).save(*args, **kwargs)

        Translation.objects.save_translations([self, ])
