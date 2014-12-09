# -*- coding: utf-8 -*-
import copy

from django.core.cache import cache
from django.db.models import signals
from django.test import TestCase
from django.test.utils import override_settings

from .. import settings
from ..models import Translation


class ModelsTest(TestCase):

    def setUp(self):
        cache.clear()
        self.translation_values = {
            'identifier': 'post',
            'object_id': 1,
            'language': 'fr',
            'field_name': 'title',
            'field_value': 'Bonjour',
        }

    def tearDown(self):
        cache.clear()

    def test_set_translation(self):
        t, c = Translation.objects.set_translation(**self.translation_values)
        self.assertTrue(c)
        t, c = Translation.objects.set_translation(**self.translation_values)
        self.assertFalse(c)

    def test_cache_keys(self):
        t, c = Translation.objects.set_translation(**self.translation_values)
        self.assertTrue(c)
        self.assertIn('cache_keys', dir(t))
        self.assertIn('_get_cache_keys', dir(t))
        self.assertEqual(t.cache_keys, ('linguist_post_1_fr_title', 'linguist_1'))

    def test_cache(self):
        # get + create = 2
        with self.assertNumQueries(2):
            t, c = Translation.objects.set_translation(**self.translation_values)

        # get id should not hit db
        with self.assertNumQueries(0):
            t = Translation.objects.get(id=1)

        # get id should hit db only once for save
        with self.assertNumQueries(1):
            t = Translation.objects.get(id=1)
            t.field_value = 'blabla'
            t.save()
            t = Translation.objects.get(id=1)
            self.assertEqual(t.field_value, 'blabla')
