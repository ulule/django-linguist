# -*- coding: utf-8 -*-
from django.db import models, IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .. import settings
from .. import utils


class TranslationManager(models.Manager):

    def get_translations(self, obj, language=None):
        """
        Shorcut method to retrieve translations for a given object.
        """
        lookup = {
            'identifier': obj.linguist_identifier,
            'object_id': obj.pk,
        }

        if language is not None:
            lookup['language'] = language

        return self.get_queryset().filter(**lookup)

    def delete_translations(self, obj, language=None):
        """
        Shortcut method to delete translations for a given object.
        """
        self.get_translations(obj, language).delete()

    def get_languages(self):
        """
        Returns all available languages.
        """
        return (self.get_queryset()
                    .values_list('language', flat=True)
                    .distinct()
                    .order_by('language'))

    def _sanitize_cached_translations(self, instances):
        """
        Sanitizes cache by assigning instance pk in object_id field.
        """
        for instance in instances:

            new_objects_keys = []
            keys_to_remove = []
            temp_id = utils.make_temp_id(instance)

            for key in instance._linguist.translations:
                object_id = key.split('_')[1]  # identifier_objectid_language_fieldname
                if object_id == temp_id:
                    new_objects_keys.append(key)

            for key in new_objects_keys:

                parts = key.split('_')
                parts[1] = '%s' % instance.pk
                new_key = '_'.join(parts)

                cached_obj = instance._linguist.translations[key]
                cached_obj.object_id = instance.pk

                instance._linguist.translations[new_key] = cached_obj
                del instance._linguist.translations[key]

            for key, cached_obj in instance._linguist.translations.iteritems():
                if cached_obj.field_value in (None, ''):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del instance._linguist.translations[key]

        return instances

    def _filter_translations_to_save(self, instances):
        """
        Takes a list of model instances and returns a tuple
        ``(to_create, to_update)``.
        """
        to_create, to_update = [], []

        for instance in instances:
            for key, cached_obj in instance._linguist.translations.iteritems():
                if cached_obj.is_new:
                    to_create.append((key, cached_obj))
                else:
                    to_update.append((key, cached_obj))

        return (to_create, to_update)

    def _prepare_translations_to_save(self, to_create, to_update):
        """
        Prepare objects for bulk create and update.
        """
        create, update = [], []

        if to_create:
            for key, cached_obj in to_create:
                create.append(self.model(**cached_obj.attrs))

        if to_update:
            for key, cached_obj in to_update:
                update.append((cached_obj.lookup, cached_obj.attrs))

        return create, update

    def save_translations(self, instances):
        """
        Saves cached translations (cached in model instances as dictionaries).
        """
        if not isinstance(instances, (list, tuple)):
            instances = [instances]

        instances = self._sanitize_cached_translations(instances)
        to_create, to_update = self._filter_translations_to_save(instances)
        create_objects, update_objects = self._prepare_translations_to_save(to_create, to_update)

        created = True
        if create_objects:
            try:
                self.bulk_create(create_objects)
            except IntegrityError:
                created = False

        if update_objects:
            for key, cached_obj in to_update:
                self.filter(**cached_obj.lookup).update(**cached_obj.attrs)

        if created:
            for key, cached_obj in to_create:
                cached_obj.is_new = False


@python_2_unicode_compatible
class Translation(models.Model):
    """
    A Translation.
    """
    identifier = models.CharField(
        max_length=100,
        verbose_name=_('identifier'),
        help_text=_('The registered model identifier.'))

    object_id = models.IntegerField(
        verbose_name=_('The object ID'),
        null=True,
        help_text=_('The object ID of this translation'))

    language = models.CharField(
        max_length=10,
        verbose_name=_('language'),
        choices=settings.SUPPORTED_LANGUAGES,
        default=settings.DEFAULT_LANGUAGE,
        help_text=_('The language for this translation'))

    field_name = models.CharField(
        max_length=100,
        verbose_name=_('field name'),
        help_text=_('The model field name for this translation.'))

    field_value = models.TextField(
        verbose_name=_('field value'),
        null=True,
        help_text=_('The translated content for the field.'))

    objects = TranslationManager()

    class Meta:
        abstract = True
        app_label = 'linguist'
        verbose_name = _('translation')
        verbose_name_plural = _('translations')
        unique_together = (('identifier', 'object_id', 'language', 'field_name'),)

    def __str__(self):
        return '%s:%s:%s:%s' % (
            self.identifier,
            self.object_id,
            self.field_name,
            self.language)
