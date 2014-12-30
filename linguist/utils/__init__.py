# -*- coding: utf-8 -*-
from .i18n import (get_language_name,
                   get_language,
                   get_fallback_language,
                   build_localized_field_name,
                   build_localized_verbose_name)

from .models import load_class, get_model_string
from .template import select_template_name
from .views import get_language_parameter, get_language_tabs


def chunks(l, n):
    """
    Yields successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i + n]
