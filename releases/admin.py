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

from django.utils.translation import get_language
from django.contrib.admin import site, ModelAdmin, StackedInline

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

class ReleaseAdmin(ModelAdmin):
    """Customised releases editing in the administration interface"""
    raw_id_fields = ('manager', 'reviewer', 'bug_manager', 'translation_manager')
    form = ReleaseForm
    inlines = (PlatformInline, TranslationsInline)
    list_display = ('version', 'is_draft', 'is_prerelease', 'project', 'parent',
                    'release_date', 'manager', 'is_translated')
    list_filter = ('project', 'version', 'status', 'is_prerelease')

    def is_translated(self, obj):
        """Returns true if this is translated into one's selected language"""
        return self and bool(obj.translations.filter(language=get_language()))
    is_translated.boolean = True
    is_translated.short_description = get_language


class PlatformTranslationsInline(StackedInline):
    """Provide translation editing while editing a platform"""
    model = PlatformTranslation
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        return PlatformTranslationInlineFormSet

class PlatformAdmin(ModelAdmin):
    """Platform editing in the admin interface"""
    raw_id_fields = ('manager',)
    form = PlatformForm
    list_display = ('__str__', 'codename', 'desc', 'keywords', 'manager', 'is_translated')
    inlines = (PlatformTranslationsInline,)

    def is_translated(self, obj):
        """Returns true if this is translated into one's selected language"""
        return self and bool(obj.translations.filter(language=get_language()))
    is_translated.boolean = True
    is_translated.short_description = get_language


class ReleasePlatformTranslationsInline(StackedInline):
    """Allow editing translations while editing ReleasePlatforms"""
    model = ReleasePlatformTranslation
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        return ReleasePlatformTranslationInlineFormSet

class ReleasePlatformAdmin(ModelAdmin):
    """Customised release-platform administration editing"""
    form = ReleasePlatformForm
    list_display = ('__str__', 'download', 'resource', 'is_translated')
    list_filter = ('release', 'platform', 'release__status')
    raw_id_fields = ('resource',)
    inlines = (ReleasePlatformTranslationsInline,)

    def is_translated(self, obj):
        """Returns true if this is translated into one's selected language"""
        return self and bool(obj.translations.filter(language=get_language()))
    is_translated.boolean = True
    is_translated.short_description = get_language

site.register(Project)
site.register(Release, ReleaseAdmin)
site.register(Platform, PlatformAdmin)
site.register(ReleasePlatform, ReleasePlatformAdmin)
site.register(ReleaseStatus)
