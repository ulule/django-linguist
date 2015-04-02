# -*- coding: utf-8 -*-
from .i18n import (get_language_name,
                   get_language,
                   get_fallback_language,
                   get_real_field_name,
                   get_fallback_field_name,
                   get_supported_languages,
                   get_language_fields,
                   activate_language,
                   build_localized_field_name,
                   build_localized_verbose_name)

from .models import load_class, get_model_string

__all__ = [
    'get_language_name',
    'get_language',
    'get_fallback_language',
    'get_real_field_name',
    'get_fallback_field_name',
    'get_supported_languages',
    'get_language_fields',
    'activate_language',
    'build_localized_field_name',
    'build_localized_verbose_name',
    'load_class',
    'get_model_string',
    'chunks',
]


def chunks(l, n):
    """
    Yields successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i + n]
