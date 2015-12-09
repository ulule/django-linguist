# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from .. import utils
from ..models import Translation

from .base import BaseTestCase
from .models import BarModel


class UtilsTest(BaseTestCase):
    """
    Tests Linguist utils.
    """

    def test_get_translation_lookup(self):
        expected = {
            'title_fr': {
                'field_name': 'title',
                'field_value': 'value',
                'identifier': 'foo',
                'language': 'fr',
            },
            'title_fr__transformer': {
                'field_name': 'title',
                'field_value__transformer': 'value',
                'identifier': 'foo',
                'language': 'fr',
            },
            'title_fr__transformer1__transformer2': {
                'field_name': 'title',
                'field_value__transformer1__transformer2': 'value',
                'identifier': 'foo',
                'language': 'fr',
            },
        }

        for k, v in expected.items():
            lookup = utils.get_translation_lookup('foo', k, 'value')
            lookup = json.loads(json.dumps(lookup,sort_keys=True))
            self.assertEqual(lookup, expected[k])
