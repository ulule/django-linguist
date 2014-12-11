# -*- coding: utf-8 -*-
from django.conf import settings


APP_NAMESPACE = 'LINGUIST'

TRANSLATION_MODEL = getattr(
    settings,
    '%s_TRANSLATION_MODEL' % APP_NAMESPACE,
    'linguist.models.translation.Translation')

SUPPORTED_LANGUAGES = getattr(
    settings,
    '%s_SUPPORTED_LANGUAGES' % APP_NAMESPACE,
    settings.LANGUAGES)

DEFAULT_LANGUAGE = getattr(
    settings,
    '%s_DEFAULT_LANGUAGE' % APP_NAMESPACE,
    settings.LANGUAGE_CODE)
