# -*- coding: utf-8 -*-
from django.core.cache import cache

from . import settings
from .models import Translation
from .utils import build_cache_key


def prefetch_translations_for_model(translation_class):
    def prefetch_translations(self):
        translations = Translation.objects.filter(
            identifier=translation_class.identifier,
            object_id=self.pk)
        for translation in translations:
            cache_key = build_cache_key(**{
                'identifier': translation.identifier,
                'object_id': self.pk,
                'language': translation.language,
                'field_name': translation.field_name,
            })
            cache.add(cache_key, self, settings.CACHE_DURATION)
    return prefetch_translations


def add_translation_methods(translation_class):
    model = translation_class.model
    model.add_to_class('prefetch_translations', prefetch_translations_for_model(translation_class))
