#
# Copyright 2015, Martin Owens <doctormo@gmail.com>
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

from django.contrib.admin import *
from ajax_select.admin import AjaxSelectAdmin

from .forms import *
from .models import *

class PlatformInline(StackedInline):
    model = ReleasePlatform
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        return PlatformInlineFormSet

class TranslationsInline(StackedInline):
    model = ReleaseTranslation
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        return TranslationInlineFormSet

class ReleaseAdmin(AjaxSelectAdmin):
    form = ReleaseForm
    inlines = (PlatformInline, TranslationsInline)
    list_display = ('version', 'is_prerelease', 'parent', 'release_date', 'manager', 'keywords', 'html_desc')
    list_filter = ('version', 'status', 'is_prerelease')


class PlatformTranslationsInline(StackedInline):
    model = PlatformTranslation
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        return PlatformTranslationInlineFormSet

class PlatformAdmin(AjaxSelectAdmin):
    form = PlatformForm
    list_display = ('__str__', 'codename', 'desc', 'keywords', 'manager')
    inlines = (PlatformTranslationsInline,)


class ReleasePlatformTranslationsInline(StackedInline):
    model = ReleasePlatformTranslation
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        return ReleasePlatformTranslationInlineFormSet

class ReleasePlatformAdmin(AjaxSelectAdmin):
    form = ReleasePlatformForm
    list_filter = ('release', 'release__status')
    inlines = (ReleasePlatformTranslationsInline,)

site.register(Release, ReleaseAdmin)
site.register(Platform, PlatformAdmin)
site.register(ReleasePlatform, ReleasePlatformAdmin)
site.register(ReleaseStatus)
