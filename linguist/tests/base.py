# -*- coding: utf-8 -*-
import mimetypes
import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase

from exam.cases import Exam
from exam.decorators import fixture, before, after

from ..models import Translation

from . import settings
from .models import Tag, Author, Article, FooModel


class Fixtures(Exam):
    """
    Base test class mixin.
    """

    @fixture
    def author(self):
        return Author.objects.create(
            name="John Doe", bio_en="I am John Doe", bio_fr="Je suis John Doe"
        )

    @fixture
    def tag(self):
        return Tag.objects.create(name_fr="tag fr", name_en="tag en")

    @fixture
    def articles(self):
        articles = []
        for i in range(10):
            article = Article.objects.create(
                author=self.author,
                slug="article-%d" % i,
                title_en="%d in EN" % i,
                content_en="%d in EN" % i,
                title_fr="%d in FR" % i,
                content_fr="%s FR" % i,
            )
            article.tags.add(self.tag)
            article.save()
            articles.append(article)
        return articles

    @fixture
    def translated_instance(self):
        m = FooModel()
        for language in self.languages:
            m.activate_language(language)
            m.title = language
            m.save()
        return m

    @property
    def languages(self):
        return [language[0] for language in settings.LANGUAGES]

    @fixture
    def translation_en(self):
        return Translation.objects.create(
            identifier="foo",
            object_id=self.instance.pk,
            language="en",
            field_name="title",
            field_value="Hello",
        )

    @fixture
    def translation_fr(self):
        return Translation.objects.create(
            identifier="foo",
            object_id=self.instance.pk,
            language="fr",
            field_name="title",
            field_value="bonjour",
        )

    @before
    def setup_models(self):
        self.instance = FooModel()
        self.instance.clear_translations_cache()

    @after
    def clear_cache(self):
        self.instance.clear_translations_cache()


class BaseTransactionTestCase(Fixtures, TransactionTestCase):
    pass


class BaseTestCase(Fixtures, TestCase):
    pass


def get_file_path(*path_nodes):
    return os.path.join(settings.BASE_PATH, "tests", "fixtures", *path_nodes)


def get_uploaded_file(*path_nodes):
    data = open(get_file_path(*path_nodes), "rb").read()
    name = path_nodes[-1]
    return SimpleUploadedFile(name, data, content_type=mimetypes.guess_type(name)[0])
