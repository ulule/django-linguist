# -*- coding: utf-8 -*-
from django.apps import AppConfig


class LinguistConfig(AppConfig):
    name = 'linguist'
    verbose_name = 'Linguist'

    def ready(self):
        super(LinguistConfig, self).ready()
