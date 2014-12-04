# -*- coding: utf-8 -*-
from django.conf import settings


APP_NAMESPACE = 'LINGUIST'

TRANSLATION_MODEL = getattr(
    settings,
    '%s_TRANSLATION_MODEL' % APP_NAMESPACE,
    'linguist.models.translation.Translation')
