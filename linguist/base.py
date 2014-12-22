# -*- coding: utf-8 -*-


class ModelTranslationBase(object):

    # The Django model to translate
    model = None

    # The unique identifier for this model (must be a string)
    identifier = None

    # Fields to translate (must be a list or tuple)
    fields = None

    # Default language to use when creating new objects
    default_language = None
