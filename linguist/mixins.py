# -*- coding: utf-8 -*-
import copy

from .cache import make_cache_key, CachedTranslation
from .models import Translation
from .utils import chunks


def set_instance_cache(instance, translations):
    """
    Sets Linguist cache for the given instance.
    """
    for translation in translations:
        cache_key = make_cache_key(instance, translation)
        if cache_key not in instance._linguist.translations:
            cached_obj = CachedTranslation(**{'instance': instance, 'translation': translation})
            instance._linguist.translation[cache_key] = cached_obj
    return instance


class ManagerMixin(object):
    """
    Linguist Manager Mixin.
    """

    def with_translations(self, fields=None, languages=None, chunks_length=None):
        """
        Prefetches translations.
        """
        qs = self.get_queryset()
        object_ids = qs.values_list('id', flat=True)

        chunks_length = chunks_length if chunks_length is not None else 1

        base_lookup = dict(identifier=self.model._linguist.identifier)

        if fields is not None:
            base_lookup['field_name__in'] = fields

        if languages is not None:
            base_lookup['language__in'] = languages

        translations = []

        for ids in chunks(object_ids, chunks_length):
            lookup = copy.copy(base_lookup)
            lookup['object_id__in'] = ids
            translations += Translation.objects.filter(**lookup)

        for instance in qs:
            instance_translations = [obj for obj in translations if obj.object_id == instance.pk]
            set_instance_cache(instance, instance_translations)


class ModelMixin(object):

    @property
    def linguist_identifier(self):
        """
        Returns Linguist's identifier for this model.
        """
        return self._linguist.identifier

    @property
    def language(self):
        """
        Returns Linguist's current language.
        """
        return self._linguist.language

    @language.setter
    def language(self, value):
        """
        Sets Linguist's current language.
        """
        self._linguist.language = value

    @property
    def default_language(self):
        """
        Returns model default language.
        """
        return self._linguist.default_language

    @default_language.setter
    def default_language(self, value):
        """
        Sets model default language.
        """
        self.language = value
        self._linguist.default_language = value

    @property
    def translatable_fields(self):
        """
        Returns Linguist's translation class fields (translatable fields).
        """
        return self._linguist.fields

    @property
    def available_languages(self):
        """
        Returns available languages.
        """
        return (Translation.objects
                           .filter(identifier=self.linguist_identifier, object_id=self.pk)
                           .values_list('language', flat=True)
                           .distinct()
                           .order_by('language'))

    @property
    def cached_translations_count(self):
        """
        Returns cached translations count.
        """
        return len(self._linguist.translations)

    def clear_translations_cache(self):
        """
        Clears Linguist cache.
        """
        self._linguist.translations.clear()

    def get_translations(self, language=None):
        """
        Returns available (saved) translations for this instance.
        """
        if not self.pk:
            return Translation.objects.none()
        return Translation.objects.get_translations(**{'obj': self, 'language': language})

    def delete_translations(self, language=None):
        """
        Deletes related translations.
        """
        return Translation.objects.delete_translations(**{'obj': self, 'language': language})

    def save(self, *args, **kwargs):
        """
        Overwrites model's ``save`` method to save translations after instance
        has been saved (required to retrieve the object ID for ``Translation``
        model).
        """
        super(ModelMixin, self).save(*args, **kwargs)
        Translation.objects.save_translations([self])
