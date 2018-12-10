# -*- coding: utf-8 -*-
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

from django.http import Http404
from django.utils.text import slugify
from django.utils.translation import get_language_from_path, ugettext_lazy as _
from django.views.generic.base import RedirectView
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import Project, Platform, Release, ReleasePlatform, CACHE, Q

class DownloadRedirect(RedirectView):
    """Attempts to redirect the user to the right page for their os"""
    permanent = False

    def get_redirect_url(self, *args, **kw):
        project = self.request.GET.get('project', None)
        language = get_language_from_path(self.request.path)
        (family, version, bits) = self.get_os()
        key = slugify('download-%s-%s-%s' % (language, family, str(version)))
        if project is not None:
            key += '#' + project
        if bits:
            key += '-%d' % bits

        url = CACHE.get(key)
        if not url:
            try:
                url = self.get_url(project, family, version, bits)
            except Release.DoesNotExist:
                raise Http404
            CACHE.set(key, url, 2 * 3600) # Two hours

        if settings.DEBUG:
            url += '?os=' + key
        return url

    def get_url(self, project, family, version, bits=None):
        # A selected release MUST have a release date AND must either
        # have no parent at all, or the parent MUST also have a release date
        qset = Release.objects.filter(release_date__isnull=False)

        if project is not None:
            qset = qset.filter(project_id=project)
        else:
            qset = qset.filter(project__default=True)

        qset = qset.filter(Q(parent__isnull=True) | Q(parent__release_date__isnull=False))
        release = qset.exclude(is_prerelease=True).latest()
        platforms = list(release.platforms.for_os(family, version, bits))

        if len(platforms) == 1:
            return platforms[0].get_absolute_url()
        elif len(set([p.platform.parent for p in platforms])) == 1:
            return platforms[0].parent.get_absolute_url()
        return release.get_absolute_url()

    def get_os(self):
        # We would use user_agent parsing, but to fair, it's dreadful at os
        # giving enough data for very basic stats, but not for downloads.
        return self._get_os(self.request.META.get('HTTP_USER_AGENT', ''))

    @staticmethod
    def _get_os(ua):
        """Parse out the operating system from the user agent"""
        ua = ua.lower().replace(')', ';')
        if 'windows' in ua:
            bits = 64 if 'wow64' in ua or 'win64' in ua else 32
            version = ua.split(' nt ', 1)[-1].split(';', 1)[0]
            return ('Windows', version, bits)
        elif 'mac os x' in ua:
            version = ua.split('mac os x ')[-1].split(';')[0].replace('_', '.')
            # Limit to a single decimal version (e.g. 10.9.3 -> 10.9)
            version = version.rsplit('.', version.count('.') - 1)[0].strip()
            return ('Mac OS X', version, 64)
        elif 'linux' in ua:
            bits = ua.split('linux')[-1].split(';')[0]
            bits = 64 if '64' in bits else 32
            version = None
            for distro in ('ubuntu', 'fedora', 'debian', 'arch'):
                if distro in ua:
                    version = distro
            return ('Linux', version, bits)

        return ('Unknown', None, None)


class ReleaseView(DetailView):
    cache_tracks = (Release, Platform)
    model = Release
    slug_field = 'version'
    slug_url_kwarg = 'version'
    template_name = 'releases/release_detail.html'

    def get_queryset(self):
        from person.models import linked_users_only
        qset = super(ReleaseView, self).get_queryset()
        if 'project' in self.kwargs:
            qset = qset.filter(project_id=self.kwargs['project'])
        else:
            qset = qset.filter(Q(project__isnull=True) | Q(project__default=True))
        qset = linked_users_only(qset, 'manager', 'reviewer', 'translation_manager', 'bug_manager')
        return qset

    def get_context_data(self, **kwargs):
        data = super(ReleaseView, self).get_context_data(**kwargs)
        selected = self.object
        (REVS, VERS, DEVEL) = range(3)
        (NAME, LIST, LATEST) = range(3)
        data['releases'] = [
            (_('Revisions'), [], 0),
            (_('Versions'), [], 1),
            (_('In Development'), [], 1),
        ]
        for rel in Release.objects.for_parent(self.object).defer('html_desc', 'release_notes', 'background'):
            # The parent id is none, so this must be a top level release
            # Like 0.91 or 0.48 etc. pre-releases and point releases will
            # have a parent_id of their master release.
            if rel.parent_id is None:
                if rel.release_date:
                    # This is a released 'master release' (Versions)
                    data['releases'][VERS][LIST].append(rel)
                else:
                    # This is an unreleased master release (in development)
                    data['releases'][DEVEL][LIST].append(rel)
                # This is the selected release or the parent of it (revisions)
                if rel.pk == selected.parent_id or rel.pk == selected.pk:
                    data['releases'][REVS][LIST].append(rel)
            else:
                # This is a point or pre-release add to 'revisions'
                data['releases'][REVS][LIST].append(rel)

        if len(data['releases'][REVS][LIST]) == 1:
            # Empty the revisions list if it's just one item
            data['releases'][REVS][LIST].pop()

        # Hide pre-release revisions if the master release is 'released'
        # We first record where in the ordered list the master release is
        # and flag if it's been released. Items that happen /after/ that
        # are pre-releases.
        is_released = False

        # When we find the spot in the list, we then want to have already
        # worked out if the selected item happened 'before' it. That way
        # selecting a pre-release will show up and won't be hidden.
        is_before = False

        for item in data['releases'][REVS][LIST]:
            if is_released or item.is_prerelease:
                # If the parent is released and the selected is before
                # tell the html to hide this item (we can use js to enable)
                item.hide = True
                data['has_pre_releases'] = True

            if item.pk == selected.pk and not is_released:
                # The selected item happens /before/ the parent/master
                # (or is the parent/master) and thus we can hide pre releases.
                is_before = True

            if item.parent_id is None and item.release_date and is_before:
                # This item is the parent/master, all items below are pre.
                is_released = True

        if self.request.GET.get('latest', False):
            data['object'] = selected.latest

        data['projects'] = Project.objects.all()
        data['platforms'] = self.object.platforms.for_level('')
        return data



class PlatformList(ReleaseView):
    template_name = 'releases/platform_list.html'

    def get_title(self):
        return _('All Platforms for %s') % str(self.object)


class PlatformView(DetailView):
    model = Platform
    slug_field = 'codename'
    slug_url_kwarg = 'platform'

    def get_context_data(self, **kwargs):
        data = super(PlatformView, self).get_context_data(**kwargs)
        obj = self.object

        data['release'] = get_object_or_404(Release, version=self.kwargs['version'])
        data['platforms'] = data['release'].platforms.for_level(obj.codename)
        data['platform'] = data['object']

        try:
            data['object'] = data['release'].platforms.get(platform__codename=obj.codename)
        except ReleasePlatform.DoesNotExist:
            data['object'] = ReleasePlatform(release=data['release'], platform=data['platform'])
        except ReleasePlatform.MultipleObjectsReturned:
            data['object'] = None

        data['object-bar'] = ['platform', 'release']
        return data


class ReleasePlatformView(DetailView):
    """Veiw a specific platform-release which is a download page"""
    title = _('Download Started')
    model = ReleasePlatform

    def get_object(self):
        """Returns the right object given the version, platform and optional projet name"""
        query = Q(release__version=self.kwargs['version'],
                  platform__codename=self.kwargs['platform'])
        if 'project' in self.kwargs:
            query &= Q(release__project_id=self.kwargs['project'])
        else:
            query &= (Q(release__project__isnull=True) | Q(release__project__default=True))

        return get_object_or_404(self.model, query)
