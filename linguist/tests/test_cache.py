# -*- coding: utf-8 -*-
from ..cache import CachedTranslation

from .base import BaseTestCase
from .translations import FooModel


class CachedTranslationTest(BaseTestCase):
    """
    Tests CachedTranslation class.
    """

    def setUp(self):
        self.create_registry()

    def test_attributes(self):
        from ..models import Translation

        fields = Translation._meta.get_all_field_names()
        fields.remove('id')

        obj = CachedTranslation()

        self.assertTrue(obj.is_new)

        for attr in fields:
            self.assertTrue(hasattr(obj, attr))
            self.assertIsNone(getattr(obj, attr))

        for attr in ('instance', 'translation'):
            self.assertIsNone(getattr(obj, attr))

    def test_instance_and_translation(self):
        from ..models import Translation

        self.instance.language = 'en'
        self.instance.title = 'Hello'
        self.instance.save()

        translation = Translation.objects.first()
        obj = CachedTranslation(**{'instance': self.instance, 'translation': translation})

        self.assertTrue(isinstance(obj.instance, FooModel))
        self.assertTrue(isinstance(obj.translation, Translation))
        self.assertEqual(obj.identifier, self.instance.linguist_identifier)
        self.assertEqual(obj.object_id, self.instance.pk)
        self.assertEqual(obj.language, translation.language)
        self.assertEqual(obj.field_name, translation.field_name)
        self.assertEqual(obj.field_value, translation.field_value)

    def test_from_object(self):
        from ..models import Translation

        self.instance.language = 'en'
        self.instance.title = 'Hello'
        self.instance.save()

        translation = Translation.objects.first()
        obj = CachedTranslation()
        obj = obj.from_object(translation)

        self.assertEqual(obj.identifier, translation.identifier)
        self.assertEqual(obj.object_id, translation.object_id)
        self.assertEqual(obj.language, translation.language)
        self.assertEqual(obj.field_name, translation.field_name)
        self.assertEqual(obj.field_value, translation.field_value)
