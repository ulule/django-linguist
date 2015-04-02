# -*- coding: utf-8 -*-
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property

try:
    from django.utils.lru_cache import lru_cache as memoize
except ImportError:
    from django.utils.functional import memoize


@memoize()
def get_translation_field_names():
    """
    Returns Translation base model field names (excepted "id" field).
    """
    from .models import Translation

    fields = Translation._meta.get_all_field_names()
    fields.remove('id')

    return fields


@python_2_unicode_compatible
class CachedTranslation(object):

    def __init__(self, **kwargs):
        self.fields = get_translation_field_names()

        attrs = self.fields + ['instance', 'translation']

        for attr in attrs:
            setattr(self, attr, None)

        self.__dict__.update(**kwargs)

        self.is_new = True
        self.has_changed = False

        if self.instance is not None:
            self.identifier = self.instance.linguist_identifier
            self.object_id = self.instance.pk

        if self.translation is not None:
            self.is_new = bool(self.translation.pk is None)
            for attr in ('language', 'field_name', 'field_value'):
                setattr(self, attr, getattr(self.translation, attr))

    @cached_property
    def attrs(self):
        """
        Returns Translation attributes to pass as kwargs for creating or updating objects.
        """
        return dict((k, getattr(self, k)) for k in self.fields)

    @cached_property
    def lookup(self):
        """
        Returns lookup for get() and filter() methods.
        """
        lookup = dict((k, getattr(self, k)) for k in self.fields)
        lookup.pop('field_value')
        return lookup

    @classmethod
    def from_object(cls, obj):
        """
        Updates values from the given object.
        """
        return cls(**dict((field, getattr(obj, field))
                          for field in get_translation_field_names()))

    def __str__(self):
        return '%s:%s:%s:%s' % (
            self.identifier,
            self.object_id,
            self.field_name,
            self.language)
