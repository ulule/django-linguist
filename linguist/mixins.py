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

    def _translations_qs(self, language=None):
        kwargs = dict(identifier=self.identifier, object_id=self.pk)
        if language:
            kwargs['language'] = language
        return Translation.objects.filter(**kwargs)

    def get_translations(self, language=None):
        return self._translations_qs(language=language)

    def delete_translations(self, language=None):
        translations = self._translations_qs
        for translation in translations:
            cache_key = get_cache_key(**{
                'identifier': self.identifier,
                'object_id': self.pk,
                'language': translation.language,
                'field_name': translation.field_name,
            })
            if cache_key in self._linguist:
                del self._linguist[cache_key]
        self._translations_qs(language=language).delete()

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
