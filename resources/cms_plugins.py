#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
#
# This file is part of the software inkscape-web, consisting of custom 
# code for the Inkscape project's django-based website.
#
# inkscape-web is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# inkscape-web is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with inkscape-web.  If not, see <http://www.gnu.org/licenses/>.
#

from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.utils.permissions import get_current_user as get_user

from .forms import ModelForm
from .models import Q, GalleryPlugin, CategoryPlugin


class GalleryForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(GalleryForm, self).__init__(*args, **kwargs)
        source = self.fields['source']
        source.queryset = source.queryset.filter(Q(user=get_user())|Q(group__in=get_user().groups.all()))

    
class CMSCategoryPlugin(CMSPluginBase):
    cache = False # Plugin cache breaks pagination
    model = CategoryPlugin
    name  = _('Inkscape Category Gallery')
    cache = settings.ENABLE_CACHING

    def get_render_template(self, context=None, instance=None, placeholder=None):
        return "resources/resource_%s.html" % instance.display

    def render(self, context, instance, placeholder):
        items = instance.source.items.filter(published=True)
        objects = items.order_by('-edited')
        if instance.limit:
            page_obj = Paginator(objects, instance.limit)
            context.update({
                'placeholder': placeholder,
                'page_obj': page_obj,
                'object_list': page_obj.page(1).object_list,
                'gallery': instance.source,
            })
        else:
            context.update({
                'placeholder': placeholder,
                'object_list': objects,
            })
        # The two templates take different variable names
        context['resources'] = context['object_list']
        return context


class CMSGalleryPlugin(CMSCategoryPlugin):
    model = GalleryPlugin
    name  = _('Inkscope Team Gallery')
    form  = GalleryForm


plugin_pool.register_plugin(CMSGalleryPlugin)
plugin_pool.register_plugin(CMSCategoryPlugin)

