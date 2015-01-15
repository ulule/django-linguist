# -*- coding: utf-8 -*-
from .. import settings
from ..utils.models import load_class


Translation = load_class(settings.TRANSLATION_MODEL)


from ..signals import *  # noqa
