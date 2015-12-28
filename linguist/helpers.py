# -*- coding: utf-8 -*-
import collections
import itertools

from . import utils


def prefetch_translations(instances, **kwargs):
    """
    Prefetches translations for the given instances.
    Can be useful for a list of instances.
    """
    from .mixins import ModelMixin

    grouped_translations = utils.get_grouped_translations(instances, **kwargs)

    for instance in instances:
        if issubclass(instance.__class__, ModelMixin) and instance.pk in grouped_translations:
            for translation in grouped_translations[instance.pk]:
                instance._linguist.set_cache(instance=instance, translation=translation)
            if populate_missing:
                instance.populate_missing_translations()
