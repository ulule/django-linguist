# -*- coding: utf-8 -*-
version = (0, 1, 1)

__version__ = '.'.join(map(str, version))

default_app_config = 'linguist.apps.LinguistConfig'

__all__ = [
    'default_app_config',
    'version',
]
