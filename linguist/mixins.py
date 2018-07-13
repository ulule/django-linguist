# -*- coding: utf-8 -*-
import copy
import six

from contextlib import contextmanager

import django
from django.db.models import Q
from django.db import models
from django.utils.functional import cached_property

from . import utils
from .cache import CachedTranslation
from .helpers import prefetch_translations


if django.VERSION >= (1, 11):
    from django.db.models.query import ModelIterable as BaseModelIterable

    class ModelIterable(BaseModelIterable):
        model = None

        def __iter__(self):
            for obj in super(ModelIterable, self).__iter__():
                if obj and not isinstance(obj, self.queryset.model):
                    yield obj
                    continue

                utils.set_object_translations_cache(obj, self.queryset)

                yield obj


class QuerySetMixin(object):
    """
    Linguist QuerySet Mixin.
    """

    def __init__(self, *args, **kwargs):
        self.init(*args, **kwargs)

        super(QuerySetMixin, self).__init__(*args, **kwargs)

        if django.VERSION >= (1, 11):
            self._iterable_class = ModelIterable

    def init(self, *args, **kwargs):
        self._prefetched_translations_cache = kwargs.pop(
            "_prefetched_translations_cache", []
        )
        self._prefetch_translations_done = kwargs.pop(
            "_prefetch_translations_done", False
        )

    def _filter_or_exclude(self, negate, *args, **kwargs):
        """
        Overrides default behavior to handle linguist fields.
        """
        from .models import Translation

        new_args = self.get_cleaned_args(args)
        new_kwargs = self.get_cleaned_kwargs(kwargs)

        translation_args = self.get_translation_args(args)
        translation_kwargs = self.get_translation_kwargs(kwargs)

        has_linguist_args = self.has_linguist_args(args)
        has_linguist_kwargs = self.has_linguist_kwargs(kwargs)

        if translation_args or translation_kwargs:
            ids = list(
                set(
                    Translation.objects.filter(
                        *translation_args, **translation_kwargs
                    ).values_list("object_id", flat=True)
                )
            )
            if ids:
                new_kwargs["id__in"] = ids

        has_kwargs = has_linguist_kwargs and not (new_kwargs or new_args)
        has_args = has_linguist_args and not (new_args or new_kwargs)

        # No translations but we looked for translations?
        # Returns empty queryset.
        if has_kwargs or has_args:
            return self._clone().none()

        return super(QuerySetMixin, self)._filter_or_exclude(
            negate, *new_args, **new_kwargs
        )

    def _clone(self, klass=None, setup=False, **kwargs):
        if django.VERSION < (1, 9):
            kwargs.update({"klass": klass, "setup": setup})

        qs = super(QuerySetMixin, self)._clone(**kwargs)
        qs._prefetched_translations_cache = self._prefetched_translations_cache
        qs._prefetch_translations_done = self._prefetch_translations_done

        return qs

    def iterator(self):
        for obj in super(QuerySetMixin, self).iterator():
            if obj and not isinstance(obj, self.model):
                yield obj
                continue

            utils.set_object_translations_cache(obj, self)

            yield obj

    @cached_property
    def concrete_field_names(self):
        """
        Returns model concrete field names.
        """
        return [f[0].name for f in self._get_concrete_fields_with_model()]

    def _get_concrete_fields_with_model(self):
        """For compatibility with Django<=1.10. Replace old
        `_meta.get_concrete_fields_with_model`.
        https://docs.djangoproject.com/en/1.10/ref/models/meta/

        """
        return [
            (f, f.model if f.model != self.model else None)
            for f in self.model._meta.get_fields()
            if f.concrete
            and (
                not f.is_relation or f.one_to_one or (f.many_to_one and f.related_model)
            )
        ]

    @cached_property
    def linguist_field_names(self):
        """
        Returns linguist field names (example: "title" and "title_fr").
        """
        return list(self.model._linguist.fields) + list(
            utils.get_language_fields(self.model._linguist.fields)
        )

    def has_linguist_kwargs(self, kwargs):
        """
        Parses the given kwargs and returns True if they contain
        linguist lookups.
        """
        for k in kwargs:
            if self.is_linguist_lookup(k):
                return True
        return False

    def has_linguist_args(self, args):
        """
        Parses the given args and returns True if they contain
        linguist lookups.
        """
        linguist_args = []
        for arg in args:
            condition = self._get_linguist_condition(arg)
            if condition:
                linguist_args.append(condition)
        return bool(linguist_args)

    def get_translation_args(self, args):
        """
        Returns linguist args from model args.
        """
        translation_args = []
        for arg in args:
            condition = self._get_linguist_condition(arg, transform=True)
            if condition:
                translation_args.append(condition)
        return translation_args

    def get_translation_kwargs(self, kwargs):
        """
        Returns linguist lookup kwargs (related to Translation model).
        """
        lks = []
        for k, v in six.iteritems(kwargs):
            if self.is_linguist_lookup(k):
                lks.append(
                    utils.get_translation_lookup(self.model._linguist.identifier, k, v)
                )

        translation_kwargs = {}
        for lk in lks:
            for k, v in six.iteritems(lk):
                if k not in translation_kwargs:
                    translation_kwargs[k] = v

        return translation_kwargs

    def is_linguist_lookup(self, lookup):
        """
        Returns true if the given lookup is a valid linguist lookup.
        """
        field = utils.get_field_name_from_lookup(lookup)

        # To keep default behavior with "FieldError: Cannot resolve keyword".
        if (
            field not in self.concrete_field_names
            and field in self.linguist_field_names
        ):
            return True

        return False

    def _get_linguist_condition(self, condition, reverse=False, transform=False):
        """
        Parses Q tree and returns linguist lookups or model lookups
        if reverse is True.
        """
        # We deal with a node
        if isinstance(condition, Q):
            children = []
            for child in condition.children:
                parsed = self._get_linguist_condition(
                    condition=child, reverse=reverse, transform=transform
                )
                if parsed is not None:
                    if (isinstance(parsed, Q) and parsed.children) or isinstance(
                        parsed, tuple
                    ):
                        children.append(parsed)

            new_condition = copy.deepcopy(condition)
            new_condition.children = children

            return new_condition

        # We are dealing with a lookup ('field', 'value').
        lookup, value = condition
        is_linguist = self.is_linguist_lookup(lookup)

        if transform and is_linguist:
            return Q(
                **utils.get_translation_lookup(
                    self.model._linguist.identifier, lookup, value
                )
            )

        if (reverse and not is_linguist) or (not reverse and is_linguist):
            return condition

    def get_cleaned_args(self, args):
        """
        Returns positional arguments for related model query.
        """
        if not args:
            return args

        cleaned_args = []
        for arg in args:
            condition = self._get_linguist_condition(arg, True)
            if condition:
                cleaned_args.append(condition)

        return cleaned_args

    def get_cleaned_kwargs(self, kwargs):
        """
        Returns concrete field lookups.
        """
        cleaned_kwargs = kwargs.copy()

        if kwargs is not None:
            for k in kwargs:
                if self.is_linguist_lookup(k):
                    del cleaned_kwargs[k]

        return cleaned_kwargs

    def with_translations(self, **kwargs):
        """
        Prefetches translations.

        Takes three optional keyword arguments:

        * ``field_names``: ``field_name`` values for SELECT IN
        * ``languages``: ``language`` values for SELECT IN
        * ``chunks_length``: fetches IDs by chunk
        """

        force = kwargs.pop("force", False)

        if self._prefetch_translations_done and force is False:
            return self

        self._prefetched_translations_cache = utils.get_grouped_translations(
            self, **kwargs
        )
        self._prefetch_translations_done = True

        return self._clone()

    def activate_language(self, language):
        """
        Activates the given ``language`` for the QuerySet instances.
        """
        utils.activate_language(self, language)
        return self


class LinguistQuerySet(QuerySetMixin, models.query.QuerySet):
    pass


class ManagerMixin(object):
    """
    Linguist Manager Mixin.
    """

    def get_queryset(self):
        return LinguistQuerySet(self.model)

    def with_translations(self, **kwargs):
        """
        Proxy for ``QuerySetMixin.with_translations()`` method.
        """
        return self.get_queryset().with_translations(**kwargs)

    def activate_language(self, language):
        """
        Proxy for ``QuerySetMixin.activate_language()`` method.
        """
        self.get_queryset().activate_language(language)


class ModelMixin(object):
    def prefetch_translations(self, *args, **kwargs):
        if not self.pk:
            return

        prefetch_translations([self], **kwargs)

        if args:
            fields = [
                f for f in self._meta.get_fields(include_hidden=True) if f.name in args
            ]
            for field in fields:
                value = getattr(self, field.name, None)
                if issubclass(value.__class__, ModelMixin):
                    value.prefetch_translations()

    def populate_missing_translations(self):
        for field in self._linguist.fields:
            if field in self._linguist.translations:
                languages = self._linguist.translations[field]
                missing_languages = list(
                    set(self._linguist.supported_languages) - set(languages.keys())
                )
                for language in missing_languages:
                    self._linguist.translations[field][language] = CachedTranslation()
            else:
                self._linguist.translations[field] = {}
                for language in self._linguist.supported_languages:
                    self._linguist.translations[field][language] = CachedTranslation()

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

        return (
            Translation.objects.filter(
                identifier=self.linguist_identifier, object_id=self.pk
            )
            .values_list("language", flat=True)
            .distinct()
            .order_by("language")
        )

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

    def _save_table(
        self,
        raw=False,
        cls=None,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        """
        Overwrites model's ``_save_table`` method to save translations after instance
        has been saved (required to retrieve the object ID for ``Translation``
        model).

        Preferred over overriding the object's ``save`` method
        to ensure that `pre_save` and ``post_save`` signals happen
        respectively before and after the translations have been saved to the database.

        Thus ``pre_save`` signals have access to the ``has_changed`` attribute on translated fields
        before the translations are saved and the attribute is reset.
        And `post_save`` signals always have access to the updated translations.
        """
        updated = super(ModelMixin, self)._save_table(
            raw=raw,
            cls=cls,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        self._linguist.decider.objects.save_translations([self])
        return updated

    def get_field_object(self, field_name, language):
        return self.__class__.__dict__[
            utils.build_localized_field_name(field_name, language)
        ].field
