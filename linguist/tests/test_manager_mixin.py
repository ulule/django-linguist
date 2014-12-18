# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .base import BaseTestCase

from ..models import Translation
from ..utils.i18n import get_cache_key


class ManagerMixinTest(BaseTestCase):
    """
    Tests the Linguist's manager mixin.
    """

    def setUp(self):
        self.create_registry()

    def test_set_instance_cache(self):
        from ..mixins import set_instance_cache

        translations = [self.translation_en, self.translation_fr]
        set_instance_cache(self.instance, translations)

        self.assertEqual(
            len(self.instance._linguist.keys()) - 2,
            Translation.objects.count())

    def test_get_translation_lookups(self):
        from ..mixins import get_translation_lookups

        lookups = get_translation_lookups(self.instance)
        self.assertEqual(lookups, {
            'identifier': self.instance.identifier,
            'object_id': self.instance.pk,
        })

        lookups = get_translation_lookups(self.instance, fields=['title', 'body'])
        self.assertEqual(lookups, {
            'identifier': self.instance.identifier,
            'object_id': self.instance.pk,
            'field_name__in': ['title', 'body'],
        })

        lookups = get_translation_lookups(self.instance, fields=['title'], languages=['en', 'fr'])
        self.assertEqual(lookups, {
            'identifier': self.instance.identifier,
            'object_id': self.instance.pk,
            'field_name__in': ['title'],
            'language__in': ['en', 'fr'],
        })
