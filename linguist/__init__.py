# -*- coding: utf-8 -*-
from .registry import register, autodiscover
from .base import ModelTranslationBase

version = (0, 1, 0)

__version__ = '.'.join(map(str, version))
__all__ = ['register', 'autodiscover', 'ModelTranslationBase']

default_app_config = 'linguist.apps.LinguistConfig'
