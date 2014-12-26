# -*- coding: utf-8 -*-
from .models import Translation
from .utils.i18n import get_cache_key


def set_instance_cache(instance, translations):
    """
    Sets Linguist cache for the given instance.
    """
    for translation in translations:

        cache_key = get_cache_key(**dict(
            identifier=instance.linguist_identifier,
            object_id=instance.pk,
            language=translation.language,
            field_name=translation.field_name))

        if cache_key not in instance._linguist:
            instance._linguist[cache_key] = dict(
                object_id=instance.pk,
                identifier=instance.linguist_identifier,
                language=translation.language,
                field_name=translation.field_name,
                field_value=translation.field_value)

    return instance


def get_translation_lookups(instance, fields=None, languages=None):
    """
    Returns a dict to pass to Translation.objects.filter().
    """
    lookups = dict(
        identifier=instance.linguist_identifier,
        object_id=instance.pk)

    if fields is not None:
        lookups['field_name__in'] = fields

    if languages is not None:
        lookups['language__in'] = languages

    return lookups


class ManagerMixin(object):
    """
    Linguist Manager Mixin.
    """

    def with_translations(self, fields=None, languages=None):
        """
        Prefetches translations.
        """
        for instance in self.get_queryset():
            lookups = get_translation_lookups(instance, fields, languages)
            translations = Translation.objects.filter(**lookups)
            set_instance_cache(instance, translations)


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
            return Translations.objects.none()

        return Translation.objects.get_object_translations(**{
            'obj': self,
            'language': language,
        })

    def delete_translations(self, language=None):
        """
        Deletes related translations.
        """
        return Translation.objects.delete_object_translations(**{
            'obj': self,
            'language': language,
        })

    def _cache_translation(self, language, field_name, value):
        """
        Caches a translation.
        """
        # Determines if object already exists in db or not
        is_new = bool(self.pk is None)

        # Assign temp pk for new objects.
        # To avoid overwriting cache keys set to None
        instance_pk = self.pk if not is_new else 'new-%s' % id(self)

        attrs = dict(
            identifier=self._linguist.identifier,
            object_id=instance_pk,
            language=language,
            field_name=field_name)

        cache_key = get_cache_key(**attrs)

        # First, try to fetch from the cache
        cached = self._linguist.translations.get(cache_key, None)

        # Cache exists? Just update the value.
        if cached is not None:
            self._linguist.translations[cache_key]['field_value'] = value
            return

        # Not cached? If it's not a new object, let's fetch it from db.
        obj = None
        if not is_new:
            try:
                obj = Translation.objects.get(**attrs)
            except Translation.DoesNotExist:
                pass

        # Object doesn't exist? Set pk to None, we'll create object later at save
        attrs['is_new'] = bool(obj is None)
        attrs['field_value'] = value

        self._linguist.translations[cache_key] = attrs

    def _get_translated_value(self, language, field_name):
        """
        Takes a language and a field name and returns the cached
        Translation instance if found, otherwise retrieves it from the database
        and cached it.
        """
        # Determines if object already exists in db or not
        is_new = True if self.pk is None else False

        # Assign temp pk for new objects.
        # To avoid overwriting cache keys set to None
        instance_pk = self.pk if not is_new else 'new-%s' % id(self)

        attrs = dict(
            identifier=self._linguist.identifier,
            object_id=instance_pk,
            language=language,
            field_name=field_name)

        cache_key = get_cache_key(**attrs)

        # First, try the fetch the value from the cache
        if cache_key in self._linguist.translations:
            return self._linguist.translations[cache_key]['field_value']

        # Not cached? If it's not a new object, let's fetch it from db.
        obj = None
        if not is_new:
            try:
                obj = Translation.objects.get(**attrs)
            except Translation.DoesNotExist:
                pass

        # Object exists: let's populate the cache and return the field value.
        if obj is not None:
            self._linguist.translations[cache_key] = attrs
            self._linguist.translations[cache_key]['is_new'] = False
            self._linguist.translations[cache_key]['field_value'] = obj.field_value
            return obj.field_value

        return None

    def save(self, *args, **kwargs):
        """
        Overwrites model's ``save`` method to save translations after instance
        has been saved (required to retrieve the object ID for ``Translation``
        model).
        """
        super(ModelMixin, self).save(*args, **kwargs)
        Translation.objects.save_translation(self)
