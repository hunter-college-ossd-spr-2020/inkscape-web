# -*- coding: utf-8 -*-
#
# Copyright 2013, Martin Owens <doctormo@gmail.com>
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
# pylint: disable=too-many-ancestors
"""
Views for resource system, adding items, entering new categories for widgets etc
"""
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.contrib import messages
from django.views.generic import DetailView, ListView, DeleteView, CreateView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.base import RedirectView
from django.template.defaultfilters import filesizeformat
from django.db.models import Q

from person.models import User, Team

from .utils import url_filefield, RemoteError
from .video_url import video_detect
from .category_views import CategoryListView
from .mixins import (
    OwnerDeleteMixin, OwnerCreateMixin, OwnerUpdateMixin,
    OwnerViewMixin, ResourceJSONEncoder,
)
from .rss import ListFeed
from .models import Category, License, Gallery, Resource, Tag
from .forms import (
    GalleryForm, GalleryMoveForm,
    ResourceForm, ResourceBaseForm, ResourceAddForm, ResourcePasteForm, ResourceLinkForm
)

class GalleryMixin(object):
    """Load up a single gallery from the kwargs"""
    pk_url_kwarg = 'gallery_id'
    model = Gallery

class DeleteGallery(GalleryMixin, OwnerDeleteMixin, DeleteView):
    """An owner of a gallery can delete it"""
    title = _("Delete Gallery")

class CreateGallery(GalleryMixin, OwnerCreateMixin, CreateView):
    """Any user can create galleries"""
    form_class = GalleryForm
    title = _("Create Gallery")

class EditGallery(GalleryMixin, OwnerUpdateMixin, UpdateView):
    """An owner of a gallery can edit it"""
    title = _("Edit Gallery")
    form_class = GalleryForm
    get_group = lambda self: None

class GalleryList(GalleryMixin, OwnerViewMixin, ListView):
    """List all galleries"""

class DeleteResource(OwnerDeleteMixin, DeleteView):
    """An owner of a resource can delete it"""
    model = Resource
    title = _("Delete")

class EditResource(OwnerUpdateMixin, UpdateView):
    """An owner of a resource can edit it"""
    model = Resource
    title = _("Edit")

    def get_form_class(self):
        return ResourceBaseForm.get_form_class(self.object)

    def get_form_kwargs(self):
        kwargs = super(EditResource, self).get_form_kwargs()
        if self.object.gallery:
            kwargs['gallery'] = self.object.gallery
        return kwargs

    def get_success_url(self):
        return self.request.POST.get('next', self.object.get_absolute_url())


class CheckResource(SingleObjectMixin, RedirectView):
    model = Resource

    def get_redirect_url(self, *args, **kwargs):
        return self.request.GET.get(
            'next', self.get_object().get_absolute_url())

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        gallery = obj.gallery

        if not request.user.is_authenticated() and gallery.user != request.user and \
                (gallery.group not in request.user.groups.all()):
            raise PermissionDenied()

        if obj.checked_by:
            obj.checked_by = None
        else:
            obj.checked_by = request.user
        obj.save()
        return super(CheckResource, self).get(request, obj=obj)

class PublishResource(OwnerUpdateMixin, DetailView):
    """Any ownerof a resource can publish it"""
    model = Resource
    title = _("Publish")

    def get(self, request, *args, **kwargs):
        item = self.get_object()
        item.published = True
        item.save()
        messages.info(self.request, _('Resource now Published'))
        return redirect(item.get_absolute_url())


class MoveResource(OwnerUpdateMixin, UpdateView):
    """Any owner of a resource and a gallery can move resources into them"""
    template_name = 'resources/resource_move.html'
    form_class = GalleryMoveForm
    model = Resource

    def get_title(self):
        if 'source' in self.kwargs:
            return _('Move to Gallery')
        return _('Copy to Gallery')

    def get_source(self):
        """Return the source gallery if needed"""
        if 'source' in self.kwargs:
            return get_object_or_404(Gallery, pk=self.kwargs['source'])
        return None

    def get_group(self):
        """This gives group members permisson to move other's resources"""
        return getattr(self.get_source(), 'group', None)

    def get_form_kwargs(self):
        kwargs = super(MoveResource, self).get_form_kwargs()
        kwargs['source'] = self.get_source()
        return kwargs

    def form_invalid(self, form):
        for error in form.errors.as_data().get('target', []):
            if error.code == 'invalid_choice':
                raise PermissionDenied()
        return super(MoveResource, self).form_invalid(form)

    def get_success_url(self):
        return self.get_object().get_absolute_url()


class UploadResource(OwnerCreateMixin, CreateView):
    """Any logged in user can create a resource"""
    form_class = ResourceForm
    model = Resource
    title = _("Upload New Resource")

    def get_form_kwargs(self):
        kwargs = super(UploadResource, self).get_form_kwargs()
        if hasattr(self, 'gallery'):
            kwargs['gallery'] = self.gallery
        return kwargs


class DropResource(UploadResource):
    """A drag and drop uploader using json"""
    template_name = 'resources/ajax/add.txt'
    content_type = 'text/plain'
    form_class = ResourceAddForm

    def form_valid(self, form):
        super().form_valid(form)
        context = self.get_context_data(item=form.instance)
        return self.render_to_response(context)

class UploadJson(UploadResource):
    """Upload with Json response"""
    form_class = ResourceAddForm

    def form_invalid(self, form):
        super().form_invalid(form)
        return JsonResponse(form.errors, status=400,
                            content_type='application/json; charset=utf-8')

    def form_valid(self, form):
        super().form_valid(form)
        return JsonResponse(form.instance.as_json(), safe=False,
                            content_type='application/json; charset=utf-8')

class QuotaJson(View):
    """Returns a Json snippet with information about a user's quota"""
    def get(self, request):
        context = {'user': 'unknown', 'quota': 0, 'used': 0}
        if request.user.is_authenticated():
            context.update({
                'user': request.user.username,
                'used': request.user.resources.disk_usage(),
                'quota': request.user.quota(),
            })
        context['remain'] = context['quota'] - context['used']
        context['used_label'] = filesizeformat(context['used'])
        context['quota_label'] = filesizeformat(context['quota'])
        return JsonResponse(context, safe=False)

class ResourcesJson(View):
    """Returns information about resources"""
    def get(self, request):
        context = {}

        qset = Resource.objects.all()
        max_num = 1
        if 'pks[]' in request.GET:
            pks = request.GET.getlist('pks[]')
            qset = qset.filter(pk__in=pks)
            max_num += len(pks)
        elif 'q' in request.GET:
            query = Q()
            for qey in request.GET.getlist('q'):
                if qey and '://' in qey:
                    try:
                        qey = self.parse_url(qey)
                    except ValueError as err:
                        context['error'] = str(err)
                        qey = ''
                    except RemoteError as err:
                        context['error'] = "Remote server error! {}".format(str(err))
                        qey = ''

                max_num += 2
                if qey.isnumeric():
                    context['pk'] = qey
                    query |= Q(pk=qey)
                elif qey:
                    context['query'] = qey
                    query |= Q(name__iexact=qey)\
                           | Q(slug__iexact=qey)\
                           | Q(download__iendswith=qey)

            if not query:
                qset = qset.none()
            else:
                qset = qset.filter(query)
        else:
            qset = qset.none()

        if qset.count() > max_num:
            context['error'] = 'Too many results (>{})'.format(max_num)
            qset = qset.none()

        context['resources'] = [resource.as_json() for resource in qset]

        return JsonResponse(context, safe=False,
                            content_type='application/json; charset=utf-8')

    def parse_url(self, query):
        """
        We want to parse a given URL and decide if it's a video URL
        or some other interesting or important URL.
        """
        is_video = video_detect(query)
        if is_video:
            # Find an existing video in our resource database that matches.
            for match in Resource.objects.filter(link__contains=is_video['id']):
                match_v = match.video
                if match_v \
                      and match_v['id'] == is_video['id'] \
                      and match_v['type'] == is_video['type']:
                    return str(match.pk)

            if self.request.user.is_authenticated():
                # Create a new video object in our resource database.
                details = video_detect(query, True)
                ret = Resource(
                    user=self.request.user,
                    name=details['title'],
                    owner_name=details['author'],
                    thumbnail=url_filefield(details['thumbnail_url'],
                                            'video_' + details['id'] + '.png'),
                    link=query, owner=False, published=False)
                ret.save()
                return str(ret.pk)

        if query.rsplit('.', 1)[-1] in ('png', 'svg', 'jpeg', 'jpg'):
            # Linked image on another website
            filename = query.split('?')[0].split('/')[-1]

            for match in Resource.objects.filter(link=query):
                return str(match.pk)

            if self.request.user.is_authenticated():
                # Create a new image link object in our resource database.
                ret = Resource(
                    user=self.request.user,
                    name='Linked Image (' + filename + ')',
                    owner_name='Internet',
                    rendering=url_filefield(query, filename),
                    link=query, owner=False, published=False)
                ret.save()
                return str(ret.pk)


        return query

class LinkToResource(UploadResource):
    """Create a link to a resource instead of an upload"""
    form_class = ResourceLinkForm
    title = _("Link to Video or Resource")

class PasteInResource(UploadResource):
    """Create a paste-bin entry instead of an upload"""
    form_class = ResourcePasteForm
    title = _("New PasteBin")

    def get_context_data(self, **kw):
        data = super().get_context_data(**kw)
        data['object'] = Category.objects.get(slug='pastebin')
        data['object']._parent = self.request.user.resources.all()
        data['object_list'] = None
        return data

class ViewResource(DetailView):
    """View a single resource, for download or just zommed in"""
    model = Resource

    def get_queryset(self):
        qset = Resource.objects.for_user(self.request.user)
        if 'username' in self.kwargs:
            qset = qset.filter(user__username=self.kwargs['username'])
        return qset

    def get_template_names(self):
        if self.request.GET.get('modal', False):
            return 'resources/resource_modal.html'
        return super().get_template_names()

    def get(self, request, *args, **kwargs):
        ret = super(ViewResource, self).get(request, *args, **kwargs)
        if self.object.is_new:
            if self.object.user == request.user:
                return redirect("edit_resource", self.object.pk)
            else:
                raise Http404()
        return ret

class TagsJson(View):
    """Json based get a list of possible tags that a resource can use"""
    def get(self, request):
        # We could leverage category to style
        # categorized tags differently in the suggestions list
        context = {"tags" : [{
            "id": tag.pk,
            "name": tag.name,
            "cat" : str(tag.category or "") or None,
        } for tag in Tag.objects.all()]}
        return JsonResponse(context, safe=False, content_type='application/json; charset=utf-8')


class VoteResource(SingleObjectMixin, OwnerCreateMixin, RedirectView):
    """Allow any logged in user to vote on a resource"""
    permanent = False
    queryset = Resource.objects.filter(published=True)
    msg = {
        'prev': _('Your previous vote has been replaced by a vote for this item.'),
        'done': _('Thank you for your vote!'),
        'ended': _('You may not vote after the contest ends.'),
        'disquo': _('You may not vote for disqualified entrires.'),
        '!begun': _('You may not vote until the contest begins.'),
        '!ready': _('You may not vote in a contest open for submissions.'),
    }

    def get_redirect_url(self, *args, **kwargs):
        return self.request.GET.get(
            'next', self.get_object().get_absolute_url())

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user.pk == request.user.pk:
            raise PermissionDenied()
        try:
            self.vote_on(obj, kwargs['like'] == '+')
        except PermissionDenied as err:
            messages.error(self.request, str(err))
        return super(VoteResource, self).get(request, obj=obj)

    def vote_on(self, item, like=True):
        """Vote on the item, say if the user likes it or not"""
        gallery = item.gallery
        msg = self.msg['done']
        if gallery and gallery.contest_submit and like:
            # Delete existing contest votes.
            for vote in self.contest_vote(item):
                resource = vote.resource
                vote.delete()
                resource.votes.refresh()
                msg = self.msg['prev']
        if like:
            item.votes.get_or_create(voter_id=self.request.user.pk)
        else:
            item.votes.filter(voter_id=self.request.user.pk).delete()
        # Update the Resource item's vote count (for easier lookup)
        item.votes.refresh()
        messages.info(self.request, msg)

    def contest_vote(self, item):
        """Attempt to vote on the item, but fail if the contest isn't running"""
        gallery = item.gallery
        today = now().date()
        # Some different rules for contest galleries
        if gallery.contest_submit > today:
            raise PermissionDenied(self.msg['!begun'])
        elif gallery.contest_voting and gallery.contest_voting > today:
            raise PermissionDenied(self.msg['!ready'])
        elif gallery.contest_finish and gallery.contest_finish < today:
            raise PermissionDenied(self.msg['ended'])
        elif gallery.contest_checks and not item.checked_by:
            raise PermissionDenied(self.msg['disquo'])
        return item.gallery.votes.filter(voter_id=self.request.user.pk)

class DownloadReadme(ViewResource):
    """The readme.txt file is generated from the resource's description"""
    template_name = 'resources/readme.txt'
    content_type = "text/plain"

class DownloadResource(ViewResource):
    """Resource download will count the downloads and then redirect users"""
    template_name = 'resources/view_text.html'

    def get(self, request, *args, **kwargs):
        func = kwargs.get('fn', None)
        item = self.get_object()
        if not item.download:
            messages.warning(request, _('There is no file to download in this resource.'))
            return redirect(item.get_absolute_url())

        # The view 'download' allows one to view an image in full screen glory
        # which is technically a download, but we count it as a view and try
        # and let the browser deal with showing the file.
        if func is None:
            if item.mime().is_text():
                return super(DownloadResource, self).get(request, *args, **kwargs)
            item.fullview += 1
            item.save(update_fields=('fullview',))
            return redirect(item.download.url)

        # Otherwise the user intends to download the file and we record it as
        # such before passing the download path to nginx for delivery using a
        # content despatch to force the browser into saving-as.
        item.downed += 1
        item.save(update_fields=('downed',))

        if func not in ['download', item.filename()]:
            messages.warning(request, _('Can not find file \'%s\', please retry download.') % func)
            return redirect(item.get_absolute_url())

        # But live now uses nginx directly to set the Content-Disposition
        # since the header will be passed to the fastly cache from nginx
        # but the sendfile method will fail because of the internal redirect.
        return redirect(item.download.url.replace('/media/', '/dl/'))

class UnpublishedGallery(ListView):
    model = Resource
    paginate_by = 20
    title = _('My Unpublished Resources')

    def get_queryset(self):
        qset = super().get_queryset()
        if self.request.user.is_authenticated():
            qset = qset.filter(published=False, is_removed=False, user=self.request.user)
        else:
            qset = qset.none()
        return qset.order_by('-edited')

class ResourceList(CategoryListView):
    """
    This listing of resources provides the backbone of all gallery and resource
    listings on the website. It provies searching as well as being used by the
    RSS feed generator.
    """
    rss_view = 'resources_rss'
    parade_view = 'resources_parade'
    model = Resource
    opts = ( # type: ignore
        ('username', 'user__username'),
        ('team', 'galleries__group__team__slug', False),
        ('gallery_id', 'galleries__id', False),
        ('tags', 'tags__name', False),
    )
    cats = ( # type: ignore
        #('media_type', _("Media Type")),
        ('category', _("Media Category"), 'get_categories'),
        ('license', _("License"), 'get_licenses'),
        ('galleries', _("Galleries"), 'get_galleries'),
    )
    order = '-liked' # type: ignore
    orders = ( # type: ignore
        ('-liked', _('Most Popular')),
        ('-viewed', _('Most Views')),
        ('-downed', _('Most Downloaded')),
        ('-edited', _('Last Updated')),
    )

    def base_queryset(self):
        qset = super(ResourceList, self).base_queryset()
        if not self.request.user.has_perm('moderation.can_moderate'):
            qset = qset.exclude(is_removed=True)
        return qset

    def get_template_names(self):
        if self.get_value('category'):
            return ['resources/resourcegallery_specific.html']
        return ['resources/resourcegallery_general.html']

    def extra_filters(self):
        if not self.is_user and not self.in_team:
            return dict(published=True)
        return {}

    @property
    def is_user(self):
        """Returns True if the user is defined in the request arguments"""
        if not hasattr(self.request, 'my_is_user'):
            username = self.request.user.username
            self.request.my_is_user = self.get_value('username') == username
        return self.request.my_is_user

    @property
    def in_team(self):
        """Returns True if the user is in a team"""
        if not hasattr(self.request, 'my_in_team'):
            if self.request.user.is_authenticated():
                teams = self.request.user.teams
            else:
                teams = Team.objects.none()
            slug = self.get_value('team')
            self.request.my_in_team = teams.filter(slug=slug).count() == 1
        return self.request.my_in_team

    def get_licenses(self):
        """Return a list of licenses"""
        return License.objects.filter(filterable=True)

    def get_categories(self):
        """Return a list of Categories"""
        return Category.objects.all()

    def get_galleries(self):
        """Return a list of galleries depending on the user/team selection"""
        if 'username' in self.kwargs:
            user = get_object_or_404(User, username=self.kwargs['username'])
            return user.galleries.exclude(status="=")
        team = self.get_value('team')
        if team:
            return get_object_or_404(Group, team__slug=team).galleries.all()
        category = self.get_value('category')
        if category:
            return Gallery.objects.filter(category__slug=category)
        return None

    def get_context_data(self, **kwargs):
        """Add all the meta data together for the template"""
        data = super(ResourceList, self).get_context_data(**kwargs)
        for key in self.kwargs:
            if data.get(key, None) is None:
                raise Http404("Item %s not found" % key)

        if 'team' in data and data['team']:
            # Our options are not yet returning the correct item
            data['team'] = get_object_or_404(Group, team__slug=data['team'])
            data['team_member'] = self.in_team
            data['object_list'].instance = data['team']
        elif 'username' in self.kwargs:
            data['is_user'] = self.is_user
            if 'username' not in data or not data['username']:
                raise Http404("User not found")
            data['object_list'].instance = data['username']

        if 'galleries' in data:
            # our options are not yet returning the correct item
            data['galleries'] = get_object_or_404(Gallery, slug=data['galleries'])
            data['object'] = data['galleries']

        if not isinstance(data.get('category', None), Category):
            data.pop('category', None)

        if 'category' in data:
            data['tag_categories'] = data['category'].tags.all()
            if not ('galleries' in data and getattr(data['galleries'], 'category', None) \
                      and not data['username'] and not data['team']):
                if 'object' in data:
                    # Set parent manually, since categories don't naturally have parents.
                    data['category']._parent = data['object']
                else:
                    data['category']._parent = data['object_list']
                data['object'] = data['category']

            # Remove media type side bar if category isn't filterable.
            if not data['category'].filterable:
                for cat in data['categories']:
                    if cat is not None and cat.cid == 'category':
                        cat[:] = [cat.value]

        if 'tags' in data:
            data['tag_clear_url'] = self.get_url(exclude='tags')

        if self.is_user or ('galleries' in data and self.in_team):
            k = {}
            if data.get('galleries', None) is not None:
                k['gallery_id'] = data['galleries'].pk
            data['upload_url'] = reverse("resource.upload", kwargs=k)
            data['upload_drop'] = reverse("resource.drop", kwargs=k)

        data['limit'] = getattr(self, 'limit', 20)
        return data

class ResourceParade(ResourceList):
    def get_template_names(self):
        return ['resources/resourcegallery_parade.html']

class GalleryView(ResourceList):
    """Allow for a special version of the resource display for galleries"""
    opts = ResourceList.opts + (('galleries', 'galleries__slug', False),) # type: ignore
    cats = (('category', _("Media Category"), 'get_categories'),) # type: ignore

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = 20

    def get_gallery(self):
        """Get the Gallery in context object"""
        if not hasattr(self, '_gallery'):
            opts = dict(self.get_value_opts)
            self._gallery = get_object_or_404(Gallery, slug=opts['galleries'])
        return self._gallery

    def get_template_names(self):
        return ['resources/resourcegallery_specific.html']

    @property
    def order(self):
        """Returns the ordering in this gallery view (the first one only)"""
        return self.orders[0][0]

    @property
    def orders(self):
        """Restrict ordering when doing a contest"""
        gallery = self.get_gallery()
        if gallery.is_contest:
            if gallery.is_submitting:
                return (('-created', _('Created Date')),)
            elif gallery.is_voting:
                self.limit = 0
                return (('?', _('Random Order')),)
            return (
                ('-liked', _('Most Votes')),
                ('-created', _('Created Date')),
            )
        return super(GalleryView, self).orders

class GalleryParade(GalleryView):
    limit = 0

    def get_template_names(self):
        return ['resources/resourcegallery_parade.html']

class ResourcePick(ResourceList):
    """A loadable picker that allows an item to be choosen"""
    def get_template_names(self):
        return ['resources/resource_picker.html']

class ResourceFeed(ListFeed):
    """A list of resources in an RSS Feed"""
    list_class = ResourceList

    @property
    def title(self):
        context = self.list.context_data
        if 'object' in context:
            return str(context['object'])
        return _("Resources Feed")

    @property
    def description(self):
        context = self.list.context_data
        if 'object' in context:
            if hasattr(context['object'], 'desc'):
                return context['object'].desc
            elif hasattr(context['object'], 'description'):
                return context['object'].description
        return "Resources RSS Feed"

class GalleryFeed(ListFeed):
    list_class = GalleryView
    image_size = '190'

    @property
    def gallery(self):
        if not hasattr(self, '_gallery'):
            self._gallery = self.list.context_data['galleries']
        return self._gallery

    link = lambda self: self.gallery.get_absolute_url()
    title = lambda self: self.gallery.name
    feed_url = lambda self: self.link() + 'rss/'
    image_url = lambda self: self.media_url(self.gallery.thumbnail_url())
    description = lambda self: self.gallery.desc or _('Gallery Resources RSS Feed')
    author_name = lambda self: self.gallery.group


class ResourceJson(ResourceList):
    """Take any list of resources, and produce json output"""
    def render_to_response(self, context, **_):
        return JsonResponse(context, encoder=ResourceJSONEncoder)

class GalleryJson(GalleryView):
    """Special version of resourcejson but for galleries"""
    def render_to_response(self, context, **_):
        return JsonResponse(context, encoder=ResourceJSONEncoder)
