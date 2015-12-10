# -*- coding: utf-8 -*-
from .. import settings
from .. import utils


Translation = utils.load_class(settings.TRANSLATION_MODEL)


from ..signals import *  # noqa
