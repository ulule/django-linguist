# -*- coding: utf-8 -*-
from collections import defaultdict
from contextlib import contextmanager
import copy
import itertools
import six

from django.utils.functional import cached_property

from . import utils


class QueryBuilder(object):

    def __init__(self, model, args, kwargs):
        self.model = model
        self.args = args
        self.kwargs = kwargs
        self.has_lookups = False

    @cached_property
    def concrete_field_names(self):
        return [f[0].name for f in self.model._meta.get_concrete_fields_with_model()]

    @cached_property
    def linguist_field_names(self):
        return (list(self.model._linguist.fields) +
                list(utils.get_language_fields(self.model._linguist.fields)))

    def get_model_lookups(self):
        new_kwargs = self.kwargs.copy()

        if self.kwargs is not None:
            for k in self.kwargs:
                if self.is_linguist_lookup(k):
                    del new_kwargs[k]

        return new_kwargs

    def get_translation_lookups(self, lookups):
        if isinstance(lookups, dict):
            lookups = [(k, v) for k, v in six.iteritems(lookups)]

        translation_lookups = []
        for k, v in lookups:
            if self.is_linguist_lookup(k):
                translation_lookups.append(utils.get_translation_lookup(
                    self.model._linguist.identifier, k, v))

        return translation_lookups

    def is_linguist_lookup(self, lookup):
        field = utils.get_field_name_from_lookup(lookup)

        # To keep default behavior with "FieldError: Cannot resolve keyword".
        if (field not in self.concrete_field_names and field in self.linguist_field_names):
            return True

        return False

    def get_query_kwargs(self):
        """
        Returns kwargs for filter_or_exclude method and True if this query
        contains valid translation lookups, otherwise False.
        """
        translation_lookups = self.get_translation_lookups(self.kwargs)
        kwargs = self.get_model_lookups()

        # Fetch related translations based on lookup fields
        if translation_lookups:
            from .models import Translation

            self.has_lookups = True

            qs = Translation.objects.all()
            for lookup in translation_lookups:
                qs = qs.filter(**lookup)
            # Only retrives object IDs
            ids = list(set(qs.values_list('object_id', flat=True)))

            # Then select in if ids is not empty
            if ids:
                kwargs['id__in'] = ids

        return kwargs


class QuerySetMixin(object):
    """
    Linguist QuerySet Mixin.
    """

    def _filter_or_exclude(self, negate, *args, **kwargs):
        """
        Overrides default behavior to handle linguist fields.
        Q complex queries are not yet supported.
        """
        builder = QueryBuilder(self.model, args, kwargs)
        new_kwargs = builder.get_query_kwargs()

        # No translations found? Empty queryset.
        if builder.has_lookups and not new_kwargs:
            return self._clone().none()

        return super(QuerySetMixin, self)._filter_or_exclude(negate, *args, **new_kwargs)

    def with_translations(self, **kwargs):
        """
        Prefetches translations.

        Takes three optional keyword arguments:

        * ``field_names``: ``field_name`` values for SELECT IN
        * ``languages``: ``language`` values for SELECT IN
        * ``chunks_length``: fetches IDs by chunk
        """
        from .models import Translation

        decider = self.model._meta.linguist.get('decider', Translation)
        identifier = self.model._meta.linguist.get('identifier', None)
        chunks_length = kwargs.get('chunks_length', None)

        if identifier is None:
            raise Exception('You must define Linguist "identifier" meta option')

        lookup = dict(identifier=identifier)

        for kwarg in ('field_names', 'languages'):
            value = kwargs.get(kwarg, None)
            if value is not None:
                if not isinstance(value, (list, tuple)):
                    value = [value]
                lookup['%s__in' % kwarg[:-1]] = value

        if chunks_length is not None:
            translations_qs = []

            for ids in utils.chunks(self.values_list('id', flat=True), chunks_length):
                ids_lookup = copy.copy(lookup)
                ids_lookup['object_id__in'] = ids
                translations_qs.append(decider.objects.filter(**ids_lookup))

            translations = itertools.chain.from_iterable(translations_qs)
        else:
            lookup['object_id__in'] = [obj.pk for obj in self]
            translations = decider.objects.filter(**lookup)

        grouped_translations = defaultdict(list)

        for obj in translations:
            grouped_translations[obj.object_id].append(obj)

        for instance in self:

            instance.clear_translations_cache()

            for translation in grouped_translations[instance.pk]:
                instance._linguist.set_cache(instance=instance, translation=translation)

        return self

    def activate_language(self, language):
        """
        Activates the given ``language`` for the QuerySet instances.
        """
        utils.activate_language(self, language)
        return self


class ManagerMixin(object):
    """
    Linguist Manager Mixin.
    """

    def get_queryset(self):
        from django.db import models
        QuerySet = type('LinguistQuerySet', (QuerySetMixin, models.query.QuerySet), {})
        return QuerySet(self.model)

    def with_translations(self, **kwargs):
        """
        Proxy for ``QuerySetMixin.with_translations()`` method.
        """
        return self.get_queryset().with_translations(**kwargs)

    def activate_language(self, language):
        """
        Proxy for ``QuerySetMixin.activate_language()`` method.
        """
        self.get_queryset().active_language(language)


class ModelMixin(object):

    @property
    def linguist_identifier(self):
        """
        Returns Linguist's identifier for this model.
        """
        return self._linguist.identifier

    @property
    def active_language(self):
        return self._linguist.language

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
        from .models import Translation

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
        from .models import Translation

        if not self.pk:
            return Translation.objects.none()

        return Translation.objects.get_translations(obj=self, language=language)

    def delete_translations(self, language=None):
        """
        Deletes related translations.
        """
        from .models import Translation

        return Translation.objects.delete_translations(obj=self, language=language)

    def activate_language(self, language):
        """
        Context manager to override the instance language.
        """
        self._linguist.language = language

    @contextmanager
    def override_language(self, language):
        """
        Context manager to override the instance language.
        """
        previous_language = self._linguist.language
        self._linguist.language = language
        yield
        self._linguist.language = previous_language

    def save(self, *args, **kwargs):
        """
        Overwrites model's ``save`` method to save translations after instance
        has been saved (required to retrieve the object ID for ``Translation``
        model).
        """
        super(ModelMixin, self).save(*args, **kwargs)

        self._linguist.decider.objects.save_translations([self, ])
