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
"""Provide some reusable mixin classes for resource views."""

import os
from urllib.parse import urljoin

from django.conf import settings

from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from .models import Resource, Gallery, Model, Group, QuerySet

class OwnerViewMixin(object):
    """Doesn't limit the view, but provides user or group access and filtering"""
    user = property(lambda self: self.kwargs.get('username', None))
    team = property(lambda self: self.kwargs.get('team', None))

    def get_context_data(self, **kwargs):
        """Add useful context to all gallery and resource views"""
        data = super(OwnerViewMixin, self).get_context_data(**kwargs)
        if self.user:
            data['user'] = get_object_or_404(get_user_model(), username=self.user)
            data['object_list'].instance = data['user']
        elif hasattr(self, 'team') and self.team:
            data['group'] = get_object_or_404(Group, team__slug=self.team)
            data['object_list'].instance = data['group']
        return data

    def get_queryset(self):
        """Returns a list of things limited to either user or group"""
        qset = super(OwnerViewMixin, self).get_queryset()
        if self.user:
            qset = qset.filter(user__username=self.user, group__isnull=True)
        elif self.team:
            qset = qset.filter(group__team__slug=self.team)
        return qset


class OwnerUpdateMixin(object):
    """Limit the get and post methods to the user or group owners"""
    def is_allowed(self):
        """Test the owner, group or user for permissions"""
        obj = self.get_object()
        group = self.get_group()
        if group is not None and group in self.request.user.groups.all():
            return True
        if self.request.user.has_perm('resources.can_curate'):
            return True
        return obj.user == self.request.user

    def get_group(self):
        """Return's the object's group owner, if it has one"""
        return getattr(self.get_object(), 'group', None)

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """ Making sure that only authors can update stories """
        if not self.is_allowed():
            if not request.user.is_authenticated() and request.method == 'GET':
                return redirect_to_login(request.build_absolute_uri())
            raise PermissionDenied()

        if 'gallery_id' in kwargs:
            self.gallery = get_object_or_404(Gallery, pk=kwargs['gallery_id'])
            group_ids = request.user.groups.values_list('pk', flat=True)
            if not self.gallery.category_id and \
              self.gallery.user_id != request.user.pk and \
              self.gallery.group_id not in group_ids:
                raise PermissionDenied()

        return super(OwnerUpdateMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Return some basic resource information when editing"""
        data = super(OwnerUpdateMixin, self).get_context_data(**kwargs)
        data.update({
            'gallery': getattr(self, 'gallery', None),
            'cancel':  self.get_next_url(),
        })
        return data

    def get_next_url(self, default=None):
        """Next url is defined by the client, where to go to next"""
        if isinstance(default, Model):
            default = default.get_absolute_url()
        return self.request.GET.get('next', \
               self.request.META.get('HTTP_REFERER', default or '/'))

    def get_success_url(self):
        """Returns the success url when an item is edited"""
        try:
            return super(OwnerUpdateMixin, self).get_success_url()
        except ValueError:
            return self.get_next_url(self.parent)


class OwnerCreateMixin(OwnerUpdateMixin):
    """Who is allowed to create things"""
    def is_allowed(self):
        return self.request.user.is_authenticated()

    def get_context_data(self, **kwargs):
        data = super(OwnerCreateMixin, self).get_context_data(**kwargs)
        if hasattr(self, 'model') and not 'object_list' in data:
            data['object_list'] = self.model.objects.all()
            data['object_list'].instance = self.request.user
        if 'gallery' in data and 'object' not in data:
            data['object'] = data['gallery']
        return data


class OwnerDeleteMixin(OwnerUpdateMixin):
    """Can the owner of a thing, delete it."""
    def get_success_url(self):
        # Called before object is deleted or edited
        obj = self.get_object().parent
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url()
        return reverse('my_profile')

class ResourceJSONEncoder(DjangoJSONEncoder):
    """Turn resource objects into serializable objects for json"""
    @property
    def domain(self):
        """Return the website's domain name"""
        from django.contrib.sites.models import Site
        return Site.objects.get().domain

    def url(self, file_obj):
        """Return the full url with domain name"""
        if file_obj:
            return file_obj.url
        return None

    def default(self, o): # pylint: disable=E0202
        if isinstance(o, QuerySet):
            return [self.default(item) for item in o]
        if isinstance(o, Resource):
            return {
                'name': o.name,
                'user': str(o.user),
                'desc': o.desc,
                'link': o.link,
                'created': o.created,
                'edited': o.edited,
                'verified': o.verified,
                'download': self.url(o.download),
                'thumbnail': self.url(o.thumbnail),
                'rendering': self.url(o.rendering),
                'signature': self.url(o.signature),
                'license': o.license.code if o.license else None,
                'extra_status': o.get_extra_status_display(),
            }
        try:
            return super().default(o)
        except TypeError:
            return None
