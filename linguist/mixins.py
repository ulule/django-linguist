# -*- coding: utf-8 -*-
from .models import Translation
from .utils.i18n import get_cache_key


def set_instance_cache(instance, translations):
    """
    Sets Linguist cache for the given instance with data from the given translations.
    """
    base_key = dict(identifier=instance._linguist.identifier, object_id=instance.pk)
    for translation in translations:
        key = dict(language=translation.language, field_name=translation.field_name)
        key.update(base_key)
        cache_key = get_cache_key(**key)
        if cache_key not in instance._linguist:
            instance._linguist[cache_key] = translation
    return instance


def get_translation_lookups(instance, fields=None, languages=None):
    """
    Returns a dict to pass to Translation.objects.filter().
    """
    lookups = dict(identifier=instance.identifier, object_id=instance.pk)
    if fields is not None:
        lookups['field_name__in'] = fields
    if languages is not None:
        lookups['language__in'] = languages
    return lookups


class ManagerMixin(object):
    """
    Linguist Manager Mixin.
    """

    def with_translations(self, instances, fields=None, languages=None):
        """
        Prefetches translations for the given model instances.
        """
        if not isinstance(instances, (list, tuple)):
            instances = [instances]

        for instance in instances:
            if not isinstance(instance, LinguistMixin):
                raise Exception('%s must be an instance of LinguistMixin' % instance)
            lookups = get_translation_lookups(instance, fields, languages)
            translations = Translation.objects.filter(**lookups)
            set_instance_cache(instance, translations)


class ModelMixin(object):

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

    @property
    def cached_translations_count(self):
        return len(self._linguist.keys()) - 2

    def _get_translations_qs(self, language=None):
        kwargs = dict(identifier=self.identifier, object_id=self.pk)
        if language:
            kwargs['language'] = language
        return Translation.objects.filter(**kwargs)

    def get_translations(self, language=None):
        return self._get_translations_qs(language=language)

    def delete_translations(self, language=None):
        translations = self._get_translations_qs(language=language)
        for translation in translations:
            cache_key = get_cache_key(**{
                'identifier': self.identifier,
                'object_id': self.pk,
                'language': translation.language,
                'field_name': translation.field_name,
            })
            if cache_key in self._linguist:
                del self._linguist[cache_key]
        translations.delete()

    def get_available_languages(self):
        identifier = self._linguist.identifier
        return (Translation.objects
                           .filter(identifier=identifier, object_id=self.pk)
                           .values_list('language', flat=True)
                           .distinct()
                           .order_by('language'))
