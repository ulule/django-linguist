# -*- coding: utf-8 -*-
from .metaclasses import ModelMeta as LinguistMeta
from .mixins import ManagerMixin as LinguistManagerMixin
from .mixins import QuerySetMixin as LinguistQuerySetMixin

version = (0, 1, 0)

__version__ = '.'.join(map(str, version))

default_app_config = 'linguist.apps.LinguistConfig'

__all__ = [
    'LinguistMeta',
    'LinguistManagerMixin',
    'LinguistQuerySetMixin',
    'default_app_config',
    'version',
]
