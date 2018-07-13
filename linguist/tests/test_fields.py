from django.db.models.fields.files import FieldFile

from linguist.tests.base import TestCase

from .models import FileModel
from .base import get_uploaded_file


class FileDescriptorTest(TestCase):
    def test_descriptor(self):
        file_model = FileModel(file=get_uploaded_file("images", "linguist-600.png"))
        f = file_model.file
        assert f.__class__ is FieldFile
        assert f.name == "linguist-600.png"

        file_model.file = "path/to/file"
        f = file_model.file
        assert f.__class__ is FieldFile
        assert f.name == "path/to/file"

        file_model.file = get_uploaded_file("images", "linguist-600.png")
        f = file_model.file
        assert f.__class__ is FieldFile
        assert f.name == "linguist-600.png"
