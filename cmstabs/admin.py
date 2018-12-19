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
from django.contrib.admin import ModelAdmin, StackedInline, site
from django.forms import ModelForm

from .models import Tab, TabCategory, ShieldPlugin

class TabForm(ModelForm):
    """Form for the Tab inlined into the shield admin"""
    class Meta:
        fields = ('order', 'tab_name', 'tab_text', 'tab_cat', 'name', 'download',
                  'user', 'license', 'link', 'banner_text', 'banner_foot',
                  'btn_text', 'btn_link', 'btn_icon')
        labels = {
            'name':     _('Background Image Name'),
            'download': _('Background Image File'),
            'user':     _('Background Author'),
            'license':  _('Background License'),
            'link':     _('Background Credit Link'),
        }

class TabInline(StackedInline):
    """Inline stack of tabs for a shield"""
    raw_id_fields = ('user',)
    form = TabForm
    model = Tab
    extra = 1

class ShieldAdmin(ModelAdmin):
    """Shield plugin admin itself"""
    model = ShieldPlugin
    inlines = [TabInline]

site.register(Tab)
site.register(TabCategory)
site.register(ShieldPlugin, ShieldAdmin)

