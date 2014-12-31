# -*- coding: utf-8 -*-
from django.db import models, IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .. import settings


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

    def save_translations(self, instances):
        """
        Saves cached translations (cached in model instances as dictionaries).
        """
        if not isinstance(instances, (list, tuple)):
            instances = [instances]

        for instance in instances:

            translations = []

            for obj in instance._linguist.translation_instances:
                obj.object_id = instance.pk
                translations.append(obj)

            to_create = [(obj, self.model(**obj.attrs)) for obj in translations if obj.is_new]
            to_update = [obj for obj in translations if not obj.is_new]

            created = True

            if to_create:
                objects = [obj for cached, obj in to_create]
                try:
                    self.bulk_create(objects)
                except IntegrityError:
                    created = False

            if to_update:
                for obj in to_update:
                    self.filter(**obj.lookup).update(**obj.attrs)

            if created:
                for cached, obj in to_create:
                    cached.is_new = False


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
        db_index=True,
        help_text=_('The object ID of this translation'))

    language = models.CharField(
        max_length=10,
        verbose_name=_('language'),
        choices=settings.SUPPORTED_LANGUAGES,
        default=settings.DEFAULT_LANGUAGE,
        db_index=True,
        help_text=_('The language for this translation'))

    field_name = models.CharField(
        max_length=100,
        verbose_name=_('field name'),
        db_index=True,
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

        unique_together = (
            ('identifier', 'object_id', 'language', 'field_name'),
        )

        index_together = [
            ['identifier', 'object_id'],
        ]

    def __str__(self):
        return '%s:%s:%s:%s' % (
            self.identifier,
            self.object_id,
            self.field_name,
            self.language)
