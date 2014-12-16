# -*- coding: utf-8 -*-
from .models import Translation
from .utils.i18n import get_cache_key


class LinguistMixin(object):

    def clear_translations_cache(self):
        self._linguist.clear()

    @property
    def identifier(self):
        return self._linguist.identifier

    @property
    def language(self):
        return self._linguist.language

    @language.setter
    def language(self, value):
        self._linguist.language = value

    def get_available_languages(self):
        identifier = self._linguist.identifier
        return (Translation.objects
                           .filter(identifier=identifier, object_id=self.pk)
                           .values_list('language', flat=True)
                           .distinct()
                           .order_by('language'))

    def prefetch_translations(self):
        identifier = self._linguist.identifier
        translations = Translation.objects.filter(identifier=identifier, object_id=self.pk)
        for translation in translations:
            cache_key = get_cache_key(**{
                'identifier': identifier,
                'object_id': self.pk,
                'language': translation.language,
                'field_name': translation.field_name,
            })
            if cache_key not in self._linguist:
                self._linguist[cache_key] = translation
