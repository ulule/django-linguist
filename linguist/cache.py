# -*- coding: utf-8 -*-
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class CachedTranslation(object):

    def __init__(self, **kwargs):
        from .models import Translation

        self.instances = ['instance', 'translation']

        self.fields = Translation._meta.get_all_field_names()
        self.fields.remove('id')

        attrs = self.fields + self.instances

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

    @property
    def attrs(self):
        """
        Returns Translation attributes to pass as kwargs for creating or updating objects.
        """
        return dict((k, getattr(self, k)) for k in self.fields)

    @property
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
        from .models import Translation

        fields = Translation._meta.get_all_field_names()
        fields.remove('id')

        return cls(**dict((field, getattr(obj, field)) for field in fields))

    def __str__(self):
        return '%s:%s:%s:%s' % (
            self.identifier,
            self.object_id,
            self.field_name,
            self.language)
