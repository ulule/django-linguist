from django.db import IntegrityError, models, transaction

from django.utils.translation import gettext_lazy as _

from .. import settings


class TranslationQuerySet(models.query.QuerySet):
    def get_translations(self, obj, language=None):
        """
        Shorcut method to retrieve translations for a given object.
        """
        lookup = {"identifier": obj.linguist_identifier, "object_id": obj.pk}

        if language is not None:
            lookup["language"] = language

        return self.get_queryset().filter(**lookup)


class TranslationManager(models.Manager):
    def get_queryset(self):
        return TranslationQuerySet(self.model)

    def get_translations(self, obj, language=None):
        return self.get_queryset().get_translations(obj, language=language)

    def delete_translations(self, obj, language=None):
        """
        Shortcut method to delete translations for a given object.
        """
        self.get_translations(obj, language).delete()

    def get_languages(self):
        """
        Returns all available languages.
        """
        return (
            self.get_queryset()
            .values_list("language", flat=True)
            .distinct()
            .order_by("language")
        )

    def save_translations(self, instances):
        """
        Saves cached translations (cached in model instances as dictionaries).
        """
        if not isinstance(instances, (list, tuple)):
            instances = [instances]

        for instance in instances:

            translations = []

            for obj in instance._linguist.translation_instances:
                if obj.field_name:
                    obj.object_id = instance.pk
                    if (obj.is_new and obj.field_value) or (
                        obj.has_changed and not obj.is_new
                    ):
                        field = instance.get_field_object(obj.field_name, obj.language)
                        if hasattr(field, "pre_save") and callable(field.pre_save):
                            obj.field_value = field.pre_save(instance, True)

                    translations.append(obj)

            to_create = [
                (obj, self.model(**obj.attrs))
                for obj in translations
                if obj.is_new and obj.field_value
            ]
            to_update = [
                obj for obj in translations if obj.has_changed and not obj.is_new
            ]
            to_delete = [obj for obj in translations if obj.deleted]

            created = True

            if to_create:
                objects = [obj for cached, obj in to_create]
                try:
                    with transaction.atomic():
                        self.bulk_create(objects)
                except IntegrityError:
                    created = False

            if to_update:
                for obj in to_update:
                    self.filter(**obj.lookup).update(field_value=obj.field_value)
                    obj.has_changed = False

            if created:
                for cached, obj in to_create:
                    cached.is_new = False
                    cached.has_changed = False

            if to_delete:
                for obj in to_delete:
                    self.filter(**obj.lookup).delete()
                    obj.has_changed = False


class Translation(models.Model):
    """
    A Translation.
    """

    identifier = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name=_("identifier"),
        help_text=_("The registered model identifier."),
    )

    object_id = models.IntegerField(
        verbose_name=_("The object ID"),
        db_index=True,
        help_text=_("The object ID of this translation"),
    )

    language = models.CharField(
        max_length=10,
        verbose_name=_("language"),
        choices=settings.SUPPORTED_LANGUAGES,
        default=settings.DEFAULT_LANGUAGE,
        db_index=True,
        help_text=_("The language for this translation"),
    )

    field_name = models.CharField(
        max_length=100,
        verbose_name=_("field name"),
        db_index=True,
        help_text=_("The model field name for this translation."),
    )

    field_value = models.TextField(
        verbose_name=_("field value"),
        null=True,
        help_text=_("The translated content for the field."),
    )

    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    objects = TranslationManager()

    class Meta:
        abstract = True

        app_label = "linguist"
        verbose_name = _("translation")
        verbose_name_plural = _("translations")

        unique_together = (("identifier", "object_id", "language", "field_name"),)

        index_together = [
            ["identifier", "object_id"],
            ["identifier", "object_id", "field_name"],
        ]

    def __str__(self):
        return "%s:%s:%s:%s" % (
            self.identifier,
            self.object_id,
            self.field_name,
            self.language,
        )
