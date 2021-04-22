# -*- coding: utf-8 -*-
import collections

from . import utils

collections_abc = getattr(collections, 'abc', collections)


def prefetch_translations(instances, **kwargs):
    """
    Prefetches translations for the given instances.
    Can be useful for a list of instances.
    """
    from .mixins import ModelMixin

    if not isinstance(instances, collections_abc.Iterable):
        instances = [instances]

    populate_missing = kwargs.get("populate_missing", True)
    grouped_translations = utils.get_grouped_translations(instances, **kwargs)

    # In the case of no translations objects
    if not grouped_translations and populate_missing:
        for instance in instances:
            instance.populate_missing_translations()

    for instance in instances:
        if (
            issubclass(instance.__class__, ModelMixin)
            and instance.pk in grouped_translations
        ):
            for translation in grouped_translations[instance.pk]:
                instance._linguist.set_cache(instance=instance, translation=translation)
            if populate_missing:
                instance.populate_missing_translations()
