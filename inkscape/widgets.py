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
            'widgets/ckeditor/ckeditor.js',
        )
        css = {
            'all': { 'widgets/ckeditor/contents.css', }
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
        super(TextEditorWidget, self).__init__(attrs)
        self.installed_plugins = installed_plugins
        self.pk = pk
        self.placeholder = placeholder
        self.plugin_language = plugin_language
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
            'language': language,
        }
        return mark_safe(render_to_string('forums/ckeditor.html', context))

    def render(self, name, value, attrs=None):
        return (
            self.render_textarea(name, value, attrs) + self.render_additions(name, value, attrs)
        )
