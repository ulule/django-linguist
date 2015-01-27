# -*- coding: utf-8 -*-
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .mixins import ModelMixin


@receiver(post_delete)
def delete_translations(sender, instance, **kwargs):
    """
    Deletes related instance's translations when instance is deleted.
    """
    if issubclass(sender, (ModelMixin, )):
        instance._linguist.decider.objects.filter(identifier=instance.linguist_identifier,
                                                  object_id=instance.pk).delete()
