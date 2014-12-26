# -*- coding: utf-8 -*-


class CachedTranslation(object):

    def __init__(self, *args, **kwargs):

        # Is a new instance (not saved in db)
        self.is_new = kwargs.get('is_new', True)

        # Translation.identifier
        self.identifier = kwargs.get('identifier', None)

        # Translation.object_id
        self.object_id = kwargs.get('object_id', None)

        # Model.language
        self.language = kwargs.get('language', None)

        # Translation.field_name
        self.field_name = kwargs.get('field_name', None)

        # Translation.field_value
        self.field_value = kwargs.get('field_value', None)

        instance = kwargs.get('instance', None)
        translation = kwargs.get('translation', None)

        if instance is not None:
            self.identifier = instance.linguist_identifier
            self.object_id = '%s' % instance.pk

        if translation is not None:
            self.language = translation.language
            self.field_name = translation.field_name
            self.field_value = translation.field_value

    @property
    def attrs(self):
        """
        Returns Translation attributes to pass as kwargs for creating or updating objects.
        """
        return {
            'identifier': self.identifier,
            'object_id': self.object_id,
            'language': self.language,
            'field_name': self.field_name,
            'field_value': self.field_value,
        }

    @property
    def lookup(self):
        """
        Returns Translation lookup to use for filter method.
        """
        lookup = {
            'identifier': self.identifier,
            'object_id': self.object_id,
        }

        if self.language is not None:
            lookup['language'] = self.language

        return lookup

    def update_from_object(self, obj):
        """
        Updates values from the given object.
        """
        fields = ('identifier', 'object_id', 'language', 'field_name', 'field_value')
        for field in fields:
            setattr(self, field, getattr(obj, field))


def make_cache_key(instance, **kwargs):
    """
    Generates translation cache key.
    """
    translation = kwargs.get('translation', None)
    language = kwargs.get('language', None)
    field_name = kwargs.get('field_name', None)

    if translation is None:
        if not (language and field_name):
            raise Exception("You must set language and field name")

    if translation is not None:
        language = translation.language
        field_name = translation.field_name

    is_new = bool(instance.pk is None)
    instance_pk = instance.pk if not is_new else 'new-%s' % id(instance)

    return '%s_%s_%s_%s' % (
        instance.linguist_identifier,
        instance_pk,
        language,
        field_name)
