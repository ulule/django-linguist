# -*- coding: utf-8 -*-
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .mixins import ModelMixin
from .models import Translation


@receiver(post_delete)
def delete_translations(sender, instance, **kwargs):
    """
    Deletes related instance's translations when instance is deleted.
    """
    if isinstance(instance, (ModelMixin, )):
        Translation.objects.filter(identifier=instance.linguist_identifier,
                                   object_id=instance.pk).delete()
