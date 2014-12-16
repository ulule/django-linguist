# -*- coding: utf-8 -*-
from django.utils import six
from django.utils.encoding import force_text
from django.utils.functional import lazy
from django.utils.translation import get_language as _get_language

from .. import settings


def get_cache_key(**kwargs):
    """
    Returns cache key.
    """
    keys = ('identifier', 'object_id', 'language', 'field_name')
    return 'linguist_%s_%s_%s_%s' % tuple(kwargs[attr] for attr in keys)


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


def build_localized_field_name(field_name, language):
    """
    Build localized field name from ``field_name`` and ``language``.
    """
    return '%s_%s' % (field_name, language.replace('-', '_'))


def _build_localized_verbose_name(verbose_name, language):
    """
    Build localized verbose name from ``verbose_name`` and ``language``.
    """
    return force_text('%s [%s]') % (force_text(verbose_name), language)

build_localized_verbose_name = lazy(_build_localized_verbose_name, six.text_type)
