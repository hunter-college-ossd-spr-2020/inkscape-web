# -*- coding: utf-8 -*-
#
# Copied from django cmsplugin text ckeditor
#
from django.forms import Textarea
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation.trans_real import get_language

class TextEditorWidget(Textarea):
    """
    Use the CKEditor to allow editing html.
    """
    class Media:
        js = (
            'forums/ckeditor/ckeditor.js',
        )
        css = {
            'all': {
                #'forums/ckeditor/contents.css',
            }
        }

    def __init__(self, attrs=None, installed_plugins=None, pk=None,
                 placeholder=None, plugin_language=None, configuration=None,
                 cancel_url=None, render_plugin_url=None, action_token=None,
                 delete_on_cancel=False):
        """
        Create a widget for editing text + plugins.

        installed_plugins is a list of plugins to display that are text_enabled
        """
        if attrs is None:
            attrs = {}

        self.ckeditor_class = 'CMS_CKEditor'
        if self.ckeditor_class not in attrs.get('class', '').join(' '):
            new_class = attrs.get('class', '') + ' %s' % self.ckeditor_class
            attrs.update({
                'class': new_class.strip()
            })
        #attrs.update({
        #    'data-ckeditor-basepath': text_settings.TEXT_CKEDITOR_BASE_PATH
        #})
        super(TextEditorWidget, self).__init__(attrs)
        self.installed_plugins = installed_plugins
        self.pk = pk
        self.placeholder = placeholder
        self.plugin_language = plugin_language
        #if configuration and getattr(settings, configuration, False):
        #    conf = deepcopy(text_settings.CKEDITOR_SETTINGS)
        #    conf.update(getattr(settings, configuration))
        #    self.configuration = conf
        #else:
        #    self.configuration = text_settings.CKEDITOR_SETTINGS
        self.cancel_url = cancel_url
        self.render_plugin_url = render_plugin_url
        self.action_token = action_token
        self.delete_on_cancel = delete_on_cancel

    def render_textarea(self, name, value, attrs=None):
        return super(TextEditorWidget, self).render(name, value, attrs)

    def render_additions(self, name, value, attrs=None):
        # id attribute is always present when rendering a widget
        ckeditor_selector = attrs['id']
        language = get_language().split('-')[0]

        #config = json.dumps(configuration, cls=DjangoJSONEncoder)
        context = {
            'ckeditor_class': self.ckeditor_class,
            'ckeditor_selector': ckeditor_selector,
            #'ckeditor_function': ckeditor_selector.replace('-', '_'),
            #'name': name,
            'language': language,
            #'settings': config.replace("{{ language }}", language),
            #'STATIC_URL': settings.STATIC_URL,
            #'CKEDITOR_BASEPATH': text_settings.TEXT_CKEDITOR_BASE_PATH,
            #'installed_plugins': self.installed_plugins,
            #'plugin_pk': self.pk,
            #'plugin_language': self.plugin_language,
            #'placeholder': self.placeholder,
            #'widget': self,
        }
        return mark_safe(render_to_string('forums/ckeditor.html', context))

    def render(self, name, value, attrs=None):
        return (
            self.render_textarea(name, value, attrs) + self.render_additions(name, value, attrs)
        )
