# -*- coding: utf-8 -*-
import copy
from operator import itemgetter
import itertools

from . import utils
from .cache import CachedTranslation
from .models import Translation


def set_instance_cache(instance, translations):
    """
    Sets Linguist cache for the given instance.
    """
    instance.clear_translations_cache()
    for translation in translations:
        instance._linguist.get_or_create_cache(**{'instance': instance, 'translation': translation})
    return instance


class ManagerMixin(object):
    """
    Linguist Manager Mixin.
    """

    def with_translations(self, **kwargs):
        """
        Prefetches translations.

        Takes three optional keyword arguments:

        * ``field_names``: ``field_name`` values for SELECT IN
        * ``languages``: ``language`` values for SELECT IN
        * ``chunks_length``: fetches IDs by chunk

        """
        qs = self.get_queryset()
        object_ids = [obj.pk for obj in qs.all()]
        chunks_length = kwargs.get('chunks_length', None)

        lookup = dict(identifier=self.model._linguist.identifier)

        for kwarg in ('field_names', 'languages'):
            value = kwargs.get(kwarg, None)
            if value is not None:
                if not isinstance(value, (list, tuple)):
                    value = [value]
                lookup['%s__in' % kwarg[:-1]] = value

        translations_qs = []

        if chunks_length is not None:
            for ids in utils.chunks(object_ids, chunks_length):
                ids_lookup = copy.copy(lookup)
                ids_lookup['object_id__in'] = ids
                translations_qs.append(Translation.objects.filter(**ids_lookup))
        else:
            lookup['object_id__in'] = object_ids
            translations_qs.append(Translation.objects.filter(**lookup))

        translations = itertools.chain.from_iterable(translations_qs)

        grouped_translations = {}
        for obj in translations:
            if obj.object_id not in grouped_translations:
                grouped_translations[obj.object_id] = []
            grouped_translations[obj.object_id].append(obj)

        for instance in qs:
            set_instance_cache(instance, grouped_translations[instance.pk])


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
        return self._linguist.translations_count

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
