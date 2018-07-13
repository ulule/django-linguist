from django.db import models
from mock import patch

from linguist.fields import files, TranslationDescriptor
from linguist.metaclasses import create_translation_field, get_translation_class_kwargs
from linguist.tests.base import TestCase


class MetaclassTest(TestCase):
    SUPPORTED_FIELDS = {}

    @patch("linguist.metaclasses.SUPPORTED_FIELDS", SUPPORTED_FIELDS)
    def test_get_translation_class_kwargs(self):
        class ClassA(object):
            pass

        class ClassB(object):
            pass

        class ClassC(ClassB, ClassA):
            pass

        self.SUPPORTED_FIELDS.update(
            {ClassA: {"k": "a"}, ClassB: {"k": "b"}, ClassC: {"k": "c"}}
        )

        kwargs = get_translation_class_kwargs(ClassA)
        assert kwargs["k"] == "a"

        kwargs = get_translation_class_kwargs(ClassB)
        assert kwargs["k"] == "b"

        kwargs = get_translation_class_kwargs(ClassC)
        assert kwargs["k"] == "c"

        # When class_c not in SUPPORTED_FIELDS, find next class in class_c.__mro__
        del self.SUPPORTED_FIELDS[ClassC]
        kwargs = get_translation_class_kwargs(ClassC)
        assert kwargs["k"] == "b"

        # Keep going up the mro
        del self.SUPPORTED_FIELDS[ClassB]
        kwargs = get_translation_class_kwargs(ClassC)
        assert kwargs["k"] == "a"

        # When no class in the provided class' mro is supported, return {}
        kwargs = get_translation_class_kwargs(ClassB)
        assert kwargs == {}

    def test_create_translation_field_has_correct_descriptor(self):
        field = create_translation_field(models.fields.CharField(), "en")
        assert field.descriptor_class == TranslationDescriptor

        field = create_translation_field(models.FileField(), "en")
        assert field.descriptor_class == files.FileTranslationDescriptor

        field = create_translation_field(models.ImageField(), "en")
        assert field.descriptor_class == files.FileTranslationDescriptor

        field = create_translation_field(models.fields.TextField(), "en")
        assert field.descriptor_class == TranslationDescriptor
