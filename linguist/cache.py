# -*- coding: utf-8 -*-


class CachedTranslation(object):

    def __init__(self, **kwargs):
        from .models import Translation

        self.is_new = kwargs.get('is_new', True)
        self.instances = ['instance', 'translation']

        self.fields = Translation._meta.get_all_field_names()
        self.fields.remove('id')

        attrs = self.fields + self.instances

        for attr in attrs:
            setattr(self, attr, None)

        self.__dict__.update(**kwargs)

        if self.instance is not None:
            self.identifier = self.instance.linguist_identifier
            self.object_id = self.instance.pk if not self.is_new else None

        if self.translation is not None:
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
        Returns Translation lookup to use for filter method.
        """
        lookup = {'identifier': self.identifier,
                  'object_id': self.object_id}

        if self.language is not None:
            lookup['language'] = self.language

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
