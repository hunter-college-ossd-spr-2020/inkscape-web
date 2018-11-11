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
"""
Administration for releases app
"""

from django.contrib.admin import site, StackedInline
from ajax_select.admin import AjaxSelectAdmin

from .forms import (
    PlatformForm, ReleaseForm, ReleasePlatformForm,
    PlatformInlineFormSet, TranslationInlineFormSet,
    PlatformTranslationInlineFormSet,
    ReleasePlatformTranslationInlineFormSet,
)
from .models import (
    Project, Platform, Release, ReleaseStatus, ReleasePlatform,
    ReleaseTranslation, PlatformTranslation, ReleasePlatformTranslation,
)

class PlatformInline(StackedInline):
    """Provide admin editing for platforms while editing releases"""
    model = ReleasePlatform
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        return PlatformInlineFormSet

class TranslationsInline(StackedInline):
    """Provide admin editing for translations while editing releases"""
    model = ReleaseTranslation
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        return TranslationInlineFormSet

class ReleaseAdmin(AjaxSelectAdmin):
    """Customised releases editing in the administration interface"""
    form = ReleaseForm
    inlines = (PlatformInline, TranslationsInline)
    list_display = ('version', 'is_prerelease', 'project', 'parent',
                    'release_date', 'manager', 'keywords', 'html_desc')
    list_filter = ('project', 'version', 'status', 'is_prerelease')


class PlatformTranslationsInline(StackedInline):
    """Provide translation editing while editing a platform"""
    model = PlatformTranslation
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        return PlatformTranslationInlineFormSet

class PlatformAdmin(AjaxSelectAdmin):
    """Platform editing in the admin interface"""
    form = PlatformForm
    list_display = ('__str__', 'codename', 'desc', 'keywords', 'manager')
    inlines = (PlatformTranslationsInline,)


class ReleasePlatformTranslationsInline(StackedInline):
    """Allow editing translations while editing ReleasePlatforms"""
    model = ReleasePlatformTranslation
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        return ReleasePlatformTranslationInlineFormSet

class ReleasePlatformAdmin(AjaxSelectAdmin):
    """Customised release-platform administration editing"""
    form = ReleasePlatformForm
    list_filter = ('release', 'release__status')
    inlines = (ReleasePlatformTranslationsInline,)

site.register(Project)
site.register(Release, ReleaseAdmin)
site.register(Platform, PlatformAdmin)
site.register(ReleasePlatform, ReleasePlatformAdmin)
site.register(ReleaseStatus)
