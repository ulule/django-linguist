# -*- coding: utf-8 -*-
import copy

from django.test import TestCase

from ..models import Translation


class ModelsTest(TestCase):

    def setUp(self):
        self.translation_values = {
            'identifier': 'post',
            'object_id': 1,
            'language': 'fr',
            'field_name': 'title',
            'field_value': 'Bonjour',
        }

    def test_get_translation(self):
        # if translation does not exists, just return None
        kwargs = copy.copy(self.translation_values)
        del kwargs['field_value']
        self.assertIsNone(Translation.objects.get_translation(**kwargs))
        # otherwise return it
        Translation.objects.create(**self.translation_values)
        self.assertTrue(Translation.objects.get_translation(**kwargs))

    def test_set_translation(self):
        t, c = Translation.objects.set_translation(**self.translation_values)
        self.assertTrue(c)
        t, c = Translation.objects.set_translation(**self.translation_values)
        self.assertFalse(c)
