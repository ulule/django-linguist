# -*- coding: utf-8 -*-

from .. import settings as settings


class TabsList(list):

    def __init__(self, seq=(), css_class=None):
        self.css_class = css_class
        self.current_is_translated = False
        self.allow_deletion = False
        super(TabsList, self).__init__(seq)


def get_language_tabs(request, current_language, available_languages, css_class=None):
    """
    Determines the language tabs to show.
    """
    tabs = TabsList(css_class=css_class)
    get = request.GET.copy()
    tab_languages = []

    base_url = '{0}://{1}{2}'.format(request.is_secure() and 'https' or 'http',
                                     request.get_host(),
                                     request.path)

    for lang_code, lang_name in settings.SUPPORTED_LANGUAGES:
        get['language'] = lang_code
        url = '{0}?{1}'.format(base_url, get.urlencode())
        status = 'empty'
        if code == current_language:
            status = 'current'
        if code in available_languages:
            status = 'available'
        tabs.append((url, lang_name, lang_code, status))
        tab_languages.append(code)

    tabs.current_is_translated = current_language in available_languages
    tabs.allow_deletion = len(available_languages) > 1

    return tabs
