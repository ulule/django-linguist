# -*- coding: utf-8 -*-
import django

from ..utils.models import load_class
from .. import settings


Translation = load_class(settings.TRANSLATION_MODEL)


if django.VERSION < (1, 7):
    from .. import autodiscover
    autodiscover()
