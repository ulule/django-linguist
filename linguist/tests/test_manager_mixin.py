# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .base import BaseTestCase

from ..models import Translation
from ..utils.i18n import get_cache_key

from .translations import FooModel


class ManagerMixinTest(BaseTestCase):
    """
    Tests the Linguist's manager mixin.
    """

    def setUp(self):
        self.create_registry()

    def test_get_translation_lookups(self):
        from ..mixins import get_translation_lookups

        lookups = get_translation_lookups(self.instance)
        self.assertEqual(lookups, {
            'identifier': self.instance.linguist_identifier,
            'object_id': self.instance.pk,
        })

        lookups = get_translation_lookups(self.instance, fields=['title', 'body'])
        self.assertEqual(lookups, {
            'identifier': self.instance.linguist_identifier,
            'object_id': self.instance.pk,
            'field_name__in': ['title', 'body'],
        })

        lookups = get_translation_lookups(self.instance, fields=['title'], languages=['en', 'fr'])
        self.assertEqual(lookups, {
            'identifier': self.instance.linguist_identifier,
            'object_id': self.instance.pk,
            'field_name__in': ['title'],
            'language__in': ['en', 'fr'],
        })

    def test_with_translations(self):
        self.assertTrue(hasattr(FooModel.objects, 'with_translations'))
        FooModel.objects.with_translations()
        for obj in FooModel.objects.all():
            self.assertTrue(len(obj._linguist.keys()) > 2)
