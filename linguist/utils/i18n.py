# -*- coding: utf-8 -*-
from django.utils import six
from django.utils.encoding import force_text
from django.utils.functional import lazy
from django.utils.translation import get_language as _get_language

from .. import settings


def get_language_name(code):
    languages = dict((lang_code, lang_name) for lang_code, lang_name in settings.SUPPORTED_LANGUAGES)
    return languages.get(code)


def get_language():
    """
    Returns an active language code that is guaranteed to be in
    settings.SUPPORTED_LANGUAGES.
    """
    lang = _get_language()
    langs = [l[0] for l in settings.SUPPORTED_LANGUAGES]
    if lang not in langs and '-' in lang:
        lang = lang.split('-')[0]
    if lang in langs:
        return lang
    return settings.DEFAULT_LANGUAGE


def get_fallback_language():
    """
    Returns the fallback language.
    """
    return settings.DEFAULT_LANGUAGE


def get_real_field_name(field, lang=None):
    if lang is None:
        lang = get_language()
    return str('%s_%s' % (field, lang.replace('-', '_')))


def get_fallback_field_name(field):
    return get_real_field_name(field, lang=get_fallback_language())


def get_supported_languages():
    """
    Returns supported languages list.
    """
    return [code.replace('-', '_') for code, name in settings.SUPPORTED_LANGUAGES]


def get_language_fields(fields):
    """
    Takes a list of fields and returns related language fields.
    """
    return ['%s_%s' % (field, lang) for field in fields
                                    for lang in get_supported_languages()]


def activate_language(instances, language):
    """
    Activates the given language for the given instances.
    """
    language = language if language in get_supported_languages() else get_fallback_language()
    for instance in instances:
        instance.activate_language(language)


def build_localized_field_name(field_name, language=None):
    """
    Build localized field name from ``field_name`` and ``language``.
    """
    if language is None:
        language = get_language()
    return '%s_%s' % (field_name, language.replace('-', '_'))


def _build_localized_verbose_name(verbose_name, language):
    """
    Build localized verbose name from ``verbose_name`` and ``language``.
    """
    return force_text('%s (%s)') % (force_text(verbose_name), language)

build_localized_verbose_name = lazy(_build_localized_verbose_name, six.text_type)
