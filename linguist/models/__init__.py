# -*- coding: utf-8 -*-
from ..utils.models import load_class
from .. import settings


Translation = load_class(settings.TRANSLATION_MODEL)


from ..signals import *  # noqa
