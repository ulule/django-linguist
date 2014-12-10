# -*- coding: utf-8 -*-
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

    def test_set_translation(self):
        t, c = Translation.objects.set_translation(**self.translation_values)
        self.assertTrue(c)
        t, c = Translation.objects.set_translation(**self.translation_values)
        self.assertFalse(c)
