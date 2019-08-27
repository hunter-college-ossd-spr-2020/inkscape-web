#
# Copyright 2015-2018, Martin Owens <doctormo@gmail.com>
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
# pylint: disable=invalid-name
#
"""Forms for releases, usually admin interfaces"""

from django.utils.translation import ugettext_lazy as _
from django.forms import (
    ModelForm, ModelChoiceField, ValidationError, inlineformset_factory
)

from inkscape.widgets import TextEditorWidget

# This is used to add a custom form to resources when editing
# an Inkscape Release upload.
from resources.forms import ResourceBaseForm, Resource

from .models import (
    Release, Platform, ReleasePlatform, ReleaseTranslation,
    PlatformTranslation, ReleasePlatformTranslation,
)

class ResourceReleaseForm(ResourceBaseForm):
    """A resource for this release, a download for it"""
    form_priority = 10
    release = ModelChoiceField(queryset=Release.objects.all())
    platform = ModelChoiceField(queryset=Platform.objects.all())

    def __init__(self, data=None, *args, **kwargs):
        kwargs['initial'] = kwargs.pop('initial', {})
        if 'instance' in kwargs:
            for rp in kwargs['instance'].releases.all():
                kwargs['initial']['release'] = rp.release
                kwargs['initial']['platform'] = rp.platform
                break
        super(ResourceReleaseForm, self).__init__(data, *args, **kwargs)

    @classmethod
    def is_valid_form(cls, obj):
        """When editing an inkscape package with the right user permissions"""
        cat = getattr(obj.category, 'slug', '') == 'inkscape-package'
        return cat and obj.user and obj.user.has_perm('releases.change_release')

    def clean(self):
        super(ResourceReleaseForm, self).clean()
        release = self.cleaned_data.get('release', None)
        platform = self.cleaned_data.get('platform', None)
        if release is None or platform is None:
            raise ValidationError(_("Release and Platform must be specified!"))

        relp = release.platforms.get_or_create(platform=platform)[0]
        if relp.resource and relp.resource != self.instance:
            raise ValidationError(_("Release Platform '%s' already has a "
                                    "package resource assigned.") % str(relp))
        self.cleaned_data['release_platform'] = relp

    def save(self, **kwargs):
        obj = super(ResourceReleaseForm, self).save(**kwargs)
        if obj.pk:
            rp = self.cleaned_data['release_platform']
            rp.resource = obj
            rp.howto = obj.link
            rp.info = obj.desc
            rp.save()
        return obj

    class Meta(ResourceBaseForm.Meta):
        model = Resource
        fields = ['name', 'desc', 'tags', 'release', 'platform', 'license',
                  'link', 'signature', 'download', 'rendering', 'published']
        required = ['name', 'license', 'release', 'platform']


class QuerySetMixin(object):
    """Allow querysets in forms to be redefined easily"""
    noop = lambda self, qs: qs

    def __init__(self, *args, **kwargs):
        super(QuerySetMixin, self).__init__(*args, **kwargs)
        for key, field in self.fields.items():
            if hasattr(field, 'queryset'):
                fn = getattr(self, '%s_queryset' % key, self.noop)
                field.queryset = fn(field.queryset)


class ReleaseForm(QuerySetMixin, ModelForm):
    def __init__(self, *args, **kwargs):
        super(ReleaseForm, self).__init__(*args, **kwargs)
        if 'release_notes' in self.fields:
            self.fields['release_notes'].widget = TextEditorWidget()

    def parent_queryset(self, qs):
        qs = qs.filter(parent__isnull=True)
        if self.instance.pk:
            qs = qs.exclude(id=self.instance.pk)
        return qs


class ReleasePlatformForm(ModelForm):
    class Meta:
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(ReleasePlatformForm, self).__init__(*args, **kwargs)
        if 'info' in self.fields:
            self.fields['info'].widget = TextEditorWidget()
        if 'resource' in self.fields:
            qs = self.fields['resource'].queryset
            qs = qs.filter(category__slug='inkscape-package')
            self.fields['resource'].queryset = qs


PlatformInlineFormSet = inlineformset_factory(
    Release, ReleasePlatform, form=ReleasePlatformForm, extra=1,
)

class TranslationForm(ModelForm):
    class Meta:
        fields = ('language', 'release_notes')

    def __init__(self, *args, **kwargs):
        super(TranslationForm, self).__init__(*args, **kwargs)
        if 'release_notes' in self.fields:
            self.fields['release_notes'].widget = TextEditorWidget()

TranslationInlineFormSet = inlineformset_factory(
    Release, ReleaseTranslation, form=TranslationForm, extra=1,
)

class PlatformForm(QuerySetMixin, ModelForm):
    class Meta:
        exclude = ('codename',)

    def parent_queryset(self, qs):
        if self.instance.pk is not None:
            non_parents = [p.pk for p in self.instance.descendants()]
            non_parents += [self.instance.pk]
            return qs.exclude(pk__in=non_parents)
        return qs

    def __init__(self, *args, **kwargs):
        super(PlatformForm, self).__init__(*args, **kwargs)
        if 'instruct' in self.fields:
            self.fields['instruct'].widget = TextEditorWidget()


class PlatformTranslationForm(ModelForm):
    class Meta:
        fields = ('language', 'name', 'desc', 'instruct')

    def __init__(self, *args, **kwargs):
        super(PlatformTranslationForm, self).__init__(*args, **kwargs)
        if 'instruct' in self.fields:
            self.fields['instruct'].widget = TextEditorWidget()

PlatformTranslationInlineFormSet = inlineformset_factory(
    Platform, PlatformTranslation, form=PlatformTranslationForm, extra=1,
)


class ReleasePlatformTranslationForm(ModelForm):
    class Meta:
        fields = ('language', 'howto', 'info')

    def __init__(self, *args, **kwargs):
        super(ReleasePlatformTranslationForm, self).__init__(*args, **kwargs)
        if 'info' in self.fields:
            self.fields['info'].widget = TextEditorWidget()

ReleasePlatformTranslationInlineFormSet = inlineformset_factory(
    ReleasePlatform, ReleasePlatformTranslation, form=ReleasePlatformTranslationForm, extra=1,
)
