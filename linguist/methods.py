# -*- coding: utf-8 -*-
from .models import Translation
from .utils import get_cache_key


def prefetch_translations_for_model(translation_class):
    def prefetch_translations(self):
        identifier = translation_class.identifier
        if not hasattr(self, '_linguist'):
            self._linguist = {}
        translations = Translation.objects.filter(
            identifier=identifier,
            object_id=self.pk)
        for translation in translations:
            cache_kwargs = {
                'identifier': identifier,
                'object_id': self.pk,
                'language': translation.language,
                'field_name': translation.field_name,
            }
            cache_key = get_cache_key(**cache_kwargs)
            if cache_key not in self._linguist:
                self._linguist[cache_key] = translation
    return prefetch_translations


def add_translation_methods(translation_class):
    model = translation_class.model
    model.add_to_class('prefetch_translations', prefetch_translations_for_model(translation_class))
