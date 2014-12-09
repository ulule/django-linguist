# -*- coding: utf-8 -*-
from django.core.cache import cache
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .. import settings
from ..utils import build_cache_key


class TranslationQuerySet(models.query.QuerySet):

    def get(self, *args, **kwargs):
        if self.query.where:
            return super(TranslationQuerySet, self).get(*args, **kwargs)
        id_fields = ('identifier', 'object_id', 'language', 'field_name')
        if len(kwargs) == 1:
            k = kwargs.keys()[0]
            if k in ('pk', 'pk__exact', 'id', 'id__exact'):
                obj = cache.get('linguist_%s' % kwargs.values()[0])
                if obj is not None:
                    return obj
        elif set(id_fields) <= set(kwargs.keys()):
            cache_key = build_cache_key(**kwargs)
            obj = cache.get(cache_key)
            if obj is not None:
                return obj
        return super(TranslationQuerySet, self).get(*args, **kwargs)

    def iterator(self):
        superiter = super(TranslationQuerySet, self).iterator()
        while True:
            obj = superiter.next()
            # Use cache.add instead of cache.set to prevent race conditions
            for key in obj.cache_keys:
                cache.add(key, obj, settings.CACHE_DURATION)
            yield obj


class TranslationManager(models.Manager):

    def get_queryset(self):
        return TranslationQuerySet(self.model)

    def get_translation(self, identifier, object_id, language, field_name):
        attrs = dict(
            identifier=identifier,
            object_id=object_id,
            language=language,
            field_name=field_name)
        obj = None
        try:
            obj = self.get(**attrs)
        except self.model.DoesNotExist:
            pass
        return obj

    def set_translation(self, identifier, object_id, language, field_name, field_value):
        created = False
        attrs = dict(
            identifier=identifier,
            object_id=object_id,
            language=language,
            field_name=field_name,
            field_value=field_value)
        try:
            obj = self.get(**attrs)
        except self.model.DoesNotExist:
            obj = self.create(**attrs)
            created = True
        if obj.field_value != field_value:
            obj.field_value = field_value
            obj.save()
        return (obj, created)

    def contribute_to_class(self, model, name):
        models.signals.post_save.connect(self._post_save, sender=model)
        models.signals.post_delete.connect(self._post_delete, sender=model)
        setattr(model, '_get_cache_keys', self._get_cache_keys)
        setattr(model, 'cache_keys', property(self._get_cache_keys))
        return super(TranslationManager, self).contribute_to_class(model, name)

    def _invalidate_cache(self, instance):
        for key in instance.cache_keys:
            cache.set(key, None, 5)

    def _post_save(self, instance, **kwargs):
        for key in instance.cache_keys:
            cache.set(key, instance, settings.CACHE_DURATION)

    def _post_delete(self, instance, **kwargs):
        self._invalidate_cache(instance)

    @staticmethod
    def _get_cache_keys(obj):
        fields = ('identifier', 'object_id', 'language', 'field_name')
        cache_key = build_cache_key(**dict((attr, getattr(obj, attr)) for attr in fields))
        return (cache_key, 'linguist_%s' % obj.id)


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
        verbose_name=_('locale'),
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
        return '%s:%d:%s:%s' % (
            self.identifier,
            self.object_id,
            self.field_name,
            self.language)
