# -*- coding: utf-8 -*-
from django.conf import settings


APP_NAMESPACE = 'LINGUIST'


TRANSLATION_MODEL = getattr(
    settings,
    '%s_TRANSLATION_MODEL' % APP_NAMESPACE,
    'linguist.models.translation.Translation')

SUPPORTED_LOCALES = getattr(
    settings,
    '%s_SUPPORTED_LOCALES' % APP_NAMESPACE,
    settings.LANGUAGES)

DEFAULT_LOCALE = getattr(
    settings,
    '%s_DEFAULT_LOCALE' % APP_NAMESPACE,
    settings.LANGUAGE_CODE)
