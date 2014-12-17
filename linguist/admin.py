# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.conf.urls import patterns, url
from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m, BaseModelAdmin
from django.contrib.admin.util import get_deleted_objects, unquote
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms import Media
from django.http import HttpResponseRedirect, Http404, HttpRequest
from django.shortcuts import render
from django.utils.encoding import iri_to_uri, force_text
from django.utils.functional import lazy
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.utils import six

from .forms import ModelTranslationForm, ModelTranslationInlineFormSet
from .mixins import LinguistMixin
from .models import Translation as LinguistTranslationModel
from .utils.views import get_language_parameter, get_language_tabs
from .utils.template import select_template_name

__all__ = (
    'BaseModelTranslationAdmin',
    'ModelTranslationAdmin',
)

_language_media = Media(css={
    'all': ('linguist/admin/language_tabs.css',)
})

_language_prepopulated_media = _language_media + Media(js=(
    'admin/js/urlify.js',
    'admin/js/prepopulate.min.js'
))

_fakeRequest = HttpRequest()


class BaseModelTranslationAdmin(BaseModelAdmin):

    form = ModelTranslationForm
    query_language_key = 'language'

    @property
    def media(self):
        has_prepopulated = len(self.get_prepopulated_fields(_fakeRequest))
        base_media = super(BaseModelTranslationAdmin, self).media
        if has_prepopulated:
            return base_media + _language_prepopulated_media
        return base_media + _language_media

    def _has_translatable_model(self):
        return issubclass(self.model, LinguistMixin)

    def _language(self, request, obj=None):
        return get_language_parameter(request, self.query_language_key, object=obj)

    def get_form_language(self, request, obj=None):
        return obj.language if obj is not None else self._language(request)

    def get_language_tabs(self, request, obj, available_languages, css_class=None):
        current_language = self.get_form_language(request, obj)
        return get_language_tabs(request, current_language, available_languages, css_class=css_class)


class ModelTranslationAdmin(BaseModelTranslationAdmin, admin.ModelAdmin):

    deletion_not_allowed_template = 'admin/linguist/deletion_not_allowed.html'
    delete_inline_translations = True

    @property
    def change_form_template(self):
        if self._has_translatable_model():
            return 'admin/linguist/change_form.html'
        return None

    def language_column(self, object):
        languages = self.get_available_languages(object)
        languages = [code for code in languages]
        return '<span class="available-languages">{0}</span>'.format(' '.join(languages))

    language_column.allow_tags = True
    language_column.short_description = _("Languages")

    def get_available_languages(self, obj):
        return obj.get_available_languages() if obj else self.model.objects.none()

    def get_object(self, request, object_id):
        obj = super(ModelTranslationAdmin, self).get_object(request, object_id)
        if obj is not None and self._has_translatable_model():
            obj.language = self._language(request, obj)
        return obj

    def get_form(self, request, obj=None, **kwargs):
        form_class = super(ModelTranslationAdmin, self).get_form(request, obj, **kwargs)
        if self._has_translatable_model():
            form_class.language = self.get_form_language(request, obj)
        return form_class

    # def get_urls(self):
    #     urlpatterns = super(TranslationAdmin, self).get_urls()
    #     if not self._has_translatable_model():
    #         return urlpatterns
    #     opts = self.model._meta
    #     info = opts.app_label, opts.model_name if django.VERSION >= (1, 7) else opts.module_name
    #     return patterns('',
    #         url(r'^(.+)/delete-translation/(.+)/$',
    #             self.admin_site.admin_view(self.delete_translation),
    #             name='{0}_{1}_delete_translation'.format(*info)
    #         ),
    #     ) + urlpatterns

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if self._has_translatable_model():
            language = self.get_form_language(request, obj)
            available_languages = self.get_available_languages(obj)
            language_tabs = self.get_language_tabs(request, obj, available_languages)
            context['language_tabs'] = language_tabs
            if language_tabs:
                context['title'] = '%s (%s)' % (context['title'], language)
            if not language_tabs.current_is_translated:
                add = True
            form_url = add_preserved_filters({
                'preserved_filters': urlencode({'language': language}),
                'opts': self.model._meta
            }, form_url)
        if 'default_change_form_template' not in context:
            context['default_change_form_template'] = self.get_change_form_base_template()
        return super(ModelTranslationAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def response_add(self, request, obj, post_url_continue=None):
        redirect = super(ModelTranslationAdmin, self).response_add(request, obj, post_url_continue)
        return self._patch_redirect(request, obj, redirect)

    def response_change(self, request, obj):
        redirect = super(ModelTranslationAdmin, self).response_change(request, obj)
        return self._patch_redirect(request, obj, redirect)

    def _patch_redirect(self, request, obj, redirect):
        if redirect.status_code not in (301, 302):
            return redirect
        uri = iri_to_uri(request.path)
        opts = self.model._meta
        info = (opts.app_label, opts.model_name if django.VERSION >= (1, 7) else opts.module_name)
        language = request.GET.get(self.query_language_key)
        if language:
            continue_urls = (uri, "../add/", reverse('admin:{0}_{1}_add'.format(*info)))
            if redirect['Location'] in continue_urls and self.query_language_key in request.GET:
                redirect['Location'] += "?{0}={1}".format(self.query_language_key, language)
        return redirect

    # @csrf_protect_m
    # def delete_translation(self, request, object_id, language):
    #     opts = self.model._meta
    #     obj = self.get_object(request, unquote(object_id))

    #     if obj is None:
    #         raise Http404

    #     deleted_objects = []
    #     perms_needed = False
    #     protected = []

    #     for obj in
    #     for qs in self.get_translation_objects(request, translation.language_code, obj=shared_obj, inlines=self.delete_inline_translations):
    #         if isinstance(qs, (list, tuple)):
    #             qs_opts = qs[0]._meta
    #         else:
    #             qs_opts = qs.model._meta

    #         (del2, perms2, protected2) = get_deleted_objects(qs, qs_opts, request.user, self.admin_site)
    #         deleted_objects += del2
    #         perms_needed = perms_needed or perms2
    #         protected += protected2

    #     if request.POST:  # The user has already confirmed the deletion.
    #         if perms_needed:
    #             raise PermissionDenied
    #         obj_display = _('{0} translation of {1}').format(lang, force_text(translation))  # in hvad: (translation.master)

    #         self.log_deletion(request, translation, obj_display)
    #         self.delete_model_translation(request, translation)
    #         self.message_user(request, _('The %(name)s "%(obj)s" was deleted successfully.') % dict(
    #             name=force_text(opts.verbose_name), obj=force_text(obj_display)
    #         ))

    #         if self.has_change_permission(request, None):
    #             return HttpResponseRedirect(reverse('admin:{0}_{1}_changelist'.format(opts.app_label, opts.model_name if django.VERSION >= (1, 7) else opts.module_name)))
    #         else:
    #             return HttpResponseRedirect(reverse('admin:index'))

    #     object_name = _('{0} Translation').format(force_text(opts.verbose_name))
    #     if perms_needed or protected:
    #         title = _("Cannot delete %(name)s") % {"name": object_name}
    #     else:
    #         title = _("Are you sure?")

    #     context = {
    #         "title": title,
    #         "object_name": object_name,
    #         "object": translation,
    #         "deleted_objects": deleted_objects,
    #         "perms_lacking": perms_needed,
    #         "protected": protected,
    #         "opts": opts,
    #         "app_label": opts.app_label,
    #     }

    #     return render(request, self.delete_confirmation_template or [
    #         "admin/%s/%s/delete_confirmation.html" % (opts.app_label, opts.object_name.lower()),
    #         "admin/%s/delete_confirmation.html" % opts.app_label,
    #         "admin/delete_confirmation.html"
    #     ], context)

    # def deletion_not_allowed(self, request, obj, language):
    #     opts = self.model._meta
    #     context = {
    #         'object': obj,
    #         'language': language,
    #         'opts': opts,
    #         'app_label': opts.app_label,
    #         'language_name': language,
    #         'object_name': force_text(opts.verbose_name),
    #     }
    #     return render(request, self.deletion_not_allowed_template, context)

    # def delete_model_translation(self, request, translation):
    #     master = translation.master
    #     for qs in self.get_translation_objects(request, translation.language_code, obj=master, inlines=self.delete_inline_translations):
    #         if isinstance(qs, (tuple, list)):
    #             # The objects are deleted one by one.
    #             # This triggers the post_delete signals and such.
    #             for obj in qs:
    #                 obj.delete()
    #         else:
    #             # Also delete translations of inlines which the user has access to.
    #             # This doesn't trigger signals, just like the regular
    #             qs.delete()

    # def get_translation_objects(self, request, language_code, obj=None, inlines=True):
    #     if obj is not None:
    #         for translations_model in obj._parler_meta.get_all_models():
    #             try:
    #                 translation = translations_model.objects.get(master=obj, language_code=language_code)
    #             except translations_model.DoesNotExist:
    #                 continue
    #             yield [translation]

    #     if inlines:
    #         for inline, qs in self._get_inline_translations(request, language, obj=obj):
    #             yield qs

    # def _get_inline_translations(self, request, language, obj=None):
    #     inline_instances = self.get_inline_instances(request, obj=obj)
    #     for inline in inline_instances:
    #         if issubclass(inline.model, LinguistMixin):
    #             fk = inline.get_formset(request, obj).fk
    #             rel_name = 'master__{0}'.format(fk.name)
    #             filters = {
    #                 'language': language,
    #                 rel_name: obj
    #             }
    #             for translations_model in inline.model._parler_meta.get_all_models():
    #                 qs = translations_model.objects.filter(**filters)
    #                 if obj is not None:
    #                     qs = qs.using(obj._state.db)
    #                 yield inline, qs

    def get_change_form_base_template(self):
        opts = self.model._meta
        app_label = opts.app_label
        return _lazy_select_template_name((
            "admin/{0}/{1}/change_form.html".format(app_label, opts.object_name.lower()),
            "admin/{0}/change_form.html".format(app_label),
            "admin/change_form.html"))

_lazy_select_template_name = lazy(select_template_name, six.text_type)


class LinguistTranslationModelAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'object_id', 'language', 'field_name')


admin.site.register(LinguistTranslationModel, LinguistTranslationModelAdmin)
