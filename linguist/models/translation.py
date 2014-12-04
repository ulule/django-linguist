# -*- coding: utf-8 -*-
from . import base


class Translation(base.Translation):
    class Meta(base.Translation.Meta):
        abstract = False
