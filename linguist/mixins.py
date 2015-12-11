# -*- coding: utf-8 -*-
from collections import defaultdict
from contextlib import contextmanager
import copy
import itertools
import six

from django.db.models import Q
from django.utils.functional import cached_property

from . import utils


class Query(object):
    """
    Query is a query builder for Linguist related models.
    """

    def __init__(self, model, args, kwargs):
        # The related model class.
        self.model = model

        # Linguist model identifier
        self.identifier = model._linguist.identifier

        # Lookups as positional arguments (typically Q instances).
        # Model.objects.filter(Q(title='foo') | Q(title='bar'))
        self.args = args

        # Lookups as keyword arguments.
        # Model.objects.filter(title='foo')
        self.kwargs = kwargs

        # This is to check if we have concrete lookups
        # AND linguist lookups to return empty queryset
        # if we have related translations but empty
        # kwargs lookups.
        self.has_linguist_kwargs = False

        # The same as above for positional arguments.
        self.has_linguist_args = False

    @cached_property
    def concrete_field_names(self):
        """
        Returns model concrete field names.
        """
        return [f[0].name for f in self.model._meta.get_concrete_fields_with_model()]

    @cached_property
    def linguist_field_names(self):
        """
        Returns linguist field names (example: "title" and "title_fr").
        """
        return (list(self.model._linguist.fields) +
                list(utils.get_language_fields(self.model._linguist.fields)))

    def get_concrete_lookups(self):
        """
        Returns concrete field lookups.
        """
        lookups = self.kwargs.copy()

        if self.kwargs is not None:
            for k in self.kwargs:
                if self.is_linguist_lookup(k):
                    del lookups[k]

        return lookups

    def get_linguist_args(self):
        """
        Returns linguist args from model args.
        """
        args = []

        for arg in self.args:
            if not isinstance(arg, Q):
                continue

            children = []
            for k, v in arg.children:
                if self.is_linguist_lookup(k):
                    children.append(Q(**utils.get_translation_lookup(self.identifier, k, v)))
                    if not self.has_linguist_args:
                        self.has_linguist_args = True

            q = copy.deepcopy(arg)
            q.children = children
            args.append(q)

        return args

    def get_linguist_kwargs(self, lookups):
        """
        Returns linguist lookup kwargs (related to Translation model).
        """
        if isinstance(lookups, dict):
            lookups = [(k, v) for k, v in six.iteritems(lookups)]

        lks = []
        for k, v in lookups:
            if self.is_linguist_lookup(k):
                lks.append(utils.get_translation_lookup(
                    self.model._linguist.identifier, k, v))

        kwargs = {}
        for lk in lks:
            for k, v in six.iteritems(lk):
                if k not in kwargs:
                    kwargs[k] = v

        if kwargs:
            self.has_linguist_kwargs = True

        return kwargs

    def is_linguist_lookup(self, lookup):
        """
        Returns true if the given lookup is a valid linguist lookup.
        """
        field = utils.get_field_name_from_lookup(lookup)

        # To keep default behavior with "FieldError: Cannot resolve keyword".
        if (field not in self.concrete_field_names and field in self.linguist_field_names):
            return True

        return False

    def get_linguist_object_ids(self, *args, **kwargs):
        """
        Returns object IDs for the given args/kwargs (directly passed
        to Translation filter).
        """
        from .models import Translation
        return list(set((Translation.objects
                           .filter(*args, **kwargs)
                           .values_list('object_id', flat=True))))

    def get_args(self):
        """
        Returns positional arguments for related model query.
        """
        if not self.args:
            return self.args

        # Make a copy
        args = list(self.args)

        # Remove linguist fields.
        for arg in args:
            if not isinstance(arg, Q):
                continue
            for k, v in arg.children:
                if self.is_linguist_lookup(k):
                    # Because we iterate over children
                    try:
                        args.pop(args.index(arg))
                    except ValueError:
                        pass

        # Add linguist object IDs.
        ids = self.get_linguist_object_ids(*self.get_linguist_args())
        if ids:
            args.append(Q(**{'id__in': ids}))

        return args

    def get_kwargs(self):
        """
        Returns keyword arguments for related model query.
        """
        kwargs = self.get_concrete_lookups()

        ids = self.get_linguist_object_ids(**self.get_linguist_kwargs(self.kwargs))
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
        """
        query = Query(self.model, args, kwargs)

        query_args = query.get_args()
        query_kwargs = query.get_kwargs()

        has_kwargs = query.has_linguist_kwargs and not query_kwargs
        has_args = query.has_linguist_args and not query_args

        # No translations but we looked for translations?
        # Returns empty queryset.
        if has_kwargs or has_args:
            return self._clone().none()

        return super(QuerySetMixin, self)._filter_or_exclude(negate, *query_args, **query_kwargs)

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
