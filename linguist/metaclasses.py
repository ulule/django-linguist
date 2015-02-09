# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.fields import NOT_PROVIDED
from django.forms.forms import pretty_name
from django.utils import six

from . import settings
from . import utils


LANGUAGE_CODE, LANGUAGE_NAME = 0, 1

SUPPORTED_FIELDS = (
    models.fields.CharField,
    models.fields.TextField,
)


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


def default_value_getter(field):
    """
    When accessing to the name of the field itself, the value
    in the current language will be returned. Unless it's set,
    the value in the default language will be returned.
    """
    def default_value_func_getter(self):
        localized_field = utils.build_localized_field_name(field, self._linguist.active_language)
        return getattr(self, localized_field)

    return default_value_func_getter


def default_value_setter(field):
    """
    When setting to the name of the field itself, the value
    in the current language will be set.
    """
    def default_value_func_setter(self, value):
        localized_field = utils.build_localized_field_name(field, self._linguist.active_language)
        setattr(self, localized_field, value)

    return default_value_func_setter


def field_factory(base_class):
    """
    Takes a field base class and wrap it with ``TranslationField`` class.
    """
    from .fields import TranslationField

    class TranslationFieldField(TranslationField, base_class):
        pass

    TranslationFieldField.__name__ = b'Translation%s' % base_class.__name__

    return TranslationFieldField


def create_translation_field(translated_field, language):
    """
    Takes the original field, a given language, a decider model and return a
    Field class for model.
    """
    cls_name = translated_field.__class__.__name__

    if not isinstance(translated_field, SUPPORTED_FIELDS):
        raise ImproperlyConfigured('%s is not supported by Linguist.' % cls_name)

    translation_class = field_factory(translated_field.__class__)

    return translation_class(translated_field=translated_field,
                             language=language)


class ModelMeta(models.base.ModelBase):

    def __new__(cls, name, bases, attrs):

        from .fields import CacheDescriptor, DefaultLanguageDescriptor
        from .mixins import ModelMixin
        from .models import Translation

        meta = None
        default_language = utils.get_fallback_language()

        if 'Meta' not in attrs or not hasattr(attrs['Meta'], 'linguist'):
            return super(ModelMeta, cls).__new__(cls, name, bases, attrs)

        validate_meta(attrs['Meta'].linguist)
        meta = attrs['Meta'].linguist
        delattr(attrs['Meta'], 'linguist')

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

        #
        # Save original fields, then delete them.
        #

        original_fields = {}

        for field in meta['fields']:

            if field not in all_fields:
                raise ImproperlyConfigured(
                    "There is no field %(field)s in model %(name)s, "
                    "as specified in Meta's translate attribute" %
                    dict(field=field, name=name))

            original_fields[field] = all_fields[field]

            if field in attrs:
                del attrs[field]

        #
        # Auto-add Mixins
        #

        bases = (ModelMixin, ) + bases

        #
        # Let's create class
        #

        new_class = super(ModelMeta, cls).__new__(cls, name, bases, attrs)

        #
        # instance._linguist / instance.default_language descriptors
        #

        setattr(new_class, '_linguist', CacheDescriptor(meta=meta))
        setattr(new_class, 'default_language', DefaultLanguageDescriptor())

        #
        # Decider
        #

        decider = meta.get('decider', Translation)

        if not hasattr(decider, 'linguist_models'):
            decider.linguist_models = []

        decider.linguist_models.append(new_class)

        #
        # Language fields
        #

        for field_name, field in six.iteritems(original_fields):

            field.name = field_name
            field.model = new_class

            if not field.verbose_name:
                field.verbose_name = pretty_name(field_name)

            for lang in settings.SUPPORTED_LANGUAGES:

                lang_code = lang[LANGUAGE_CODE]
                lang_attr = create_translation_field(field, lang_code)
                lang_attr_name = utils.get_real_field_name(field_name, lang_code)

                if lang_code != default_language:
                    if not lang_attr.null and lang_attr.default is NOT_PROVIDED:
                        lang_attr.null = True
                    if not lang_attr.blank:
                        lang_attr.blank = True

                lang_attr.contribute_to_class(new_class, lang_attr_name)

            setattr(new_class,
                    field_name,
                    property(default_value_getter(field_name), default_value_setter(field_name)))

        #
        # Linguist Meta
        #

        new_class._meta.linguist = meta

        return new_class
