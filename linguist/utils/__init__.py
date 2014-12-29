# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .i18n import (get_language_name,
                   get_language,
                   get_fallback_language,
                   build_localized_field_name,
                   build_localized_verbose_name)

from .models import load_class, get_model_string
from .template import select_template_name
from .views import get_language_parameter, get_language_tabs


def make_temp_id(instance):
    """
    Takes a instance and returns a temp ID for new objects cache keys.
    """
    import hashlib
    return hashlib.sha1('%s' % id(instance)).hexdigest()


def make_cache_key(**kwargs):
    """
    Generates translation cache key.
    """
    instance = kwargs.get('instance', None)
    translation = kwargs.get('translation', None)
    language = kwargs.get('language', None)
    field_name = kwargs.get('field_name', None)

    if instance is None:
        raise Exception("You must give the instance")

    if translation is None:
        if not (language and field_name):
            raise Exception("You must set language and field name")

    if translation is not None:
        language = translation.language
        field_name = translation.field_name

    is_new = bool(instance.pk is None)
    instance_pk = instance.pk if not is_new else make_temp_id(instance)

    return '%s_%s_%s_%s' % (
        instance.linguist_identifier,
        instance_pk,
        language,
        field_name)


def chunks(l, n):
    """
    Yields successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i + n]
