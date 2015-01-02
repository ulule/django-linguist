# -*- coding: utf-8 -*_
from django import forms

from . import utils
from .models import Translation

__all__ = [
    'ModelTranslationFormMixin',
    'ModelTranslationForm',
]


class ModelTranslationFormMixin(object):
    """
    Base methods added to ``ModelTranslationForm``.
    """
    language = None

    def __init__(self, *args, **kwargs):

        super(ModelTranslationFormMixin, self).__init__(*args, **kwargs)

        instance = kwargs.get('instance', None)

        if self.language is None:
            self.language = utils.get_language()

        if instance is not None:
            self.instance.language = self.language


class ModelTranslationForm(ModelTranslationFormMixin, forms.ModelForm):
    pass
