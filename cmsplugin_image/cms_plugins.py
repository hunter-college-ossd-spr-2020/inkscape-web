# -*- coding: utf-8 -*-

from urllib.parse import urljoin

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import Image

class PicturePlugin(CMSPluginBase):
    """
    Compatible replacement for djangocms-picture,

    we use the same name, template name and icon name.
    """
    model = Image
    name = _("Picture")
    render_template = "cms/plugins/picture.html"
    text_enabled = True

    def render(self, context, instance, placeholder):
        if instance.url:
            link = instance.url
        elif instance.page_link:
            link = instance.page_link.get_absolute_url()
        else:
            link = ""
        context.update({
            'picture': instance,
            'link': link,
            'placeholder': placeholder
        })
        return context

    def icon_src(self, instance):
        if getattr(settings, 'PICTURE_FULL_IMAGE_AS_ICON', False):
            return instance.image.url
        return urljoin(settings.STATIC_URL, "cms/img/icons/plugins/picture.png")

plugin_pool.register_plugin(PicturePlugin)
