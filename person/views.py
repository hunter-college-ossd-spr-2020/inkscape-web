# -*- coding: utf-8 -*-
#
# Copyright 2014-2017, Martin Owens <doctormo@gmail.com>
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

from django.views.generic import UpdateView, DetailView, ListView, RedirectView, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404

from .models import User, Team
from .forms import UserForm, AgreeToClaForm, Permission, TeamAdminForm
from .mixins import LoginRequiredMixin, NeverCacheMixin, UserMixin, NextUrlMixin

class AgreeToCla(NeverCacheMixin, NextUrlMixin, UserMixin, UpdateView):
    template_name = 'person/cla-agree.html'
    title = _('Contributors License Agreement')
    form_class = AgreeToClaForm

class EditProfile(NeverCacheMixin, NextUrlMixin, UserMixin, UpdateView):
    title = _('Edit User Profile')
    form_class = UserForm

class UserDetail(DetailView):
    template_name  = 'person/user_detail.html'
    slug_url_kwarg = 'username'
    slug_field     = 'username'
    model = User

    def get_object(self, **kwargs):
        user = super(UserDetail, self).get_object(**kwargs)
        user.visited_by(self.request.user)
        return user

class UserGPGKey(UserDetail):
    template_name = 'person/gpgkey.txt'
    content_type = "text/plain"

class MyProfile(NeverCacheMixin, UserMixin, UserDetail):
    pass
  
class Welcome(UserMixin, TemplateView):
    template_name = 'registration/welcome.html'
    title = _('Welcome')

# ====== FRIENDSHIP VIEWS =========== #

class MakeFriend(NeverCacheMixin, LoginRequiredMixin, SingleObjectMixin, RedirectView):
    slug_url_kwarg = 'username'
    slug_field     = 'username'
    model          = User
    permanent      = False

    def get_object(self):
        user = SingleObjectMixin.get_object(self)
        (obj, new) = self.request.user.friends.get_or_create(user=user)
        if new:
            messages.success(self.request, "Friendship created with %s" % str(user))
        else:
            messages.error(self.request, "Already a friend with %s" % str(user))
        return user

    def get_redirect_url(self, **kwargs):
        return self.get_object().get_absolute_url()

class LeaveFriend(MakeFriend):
    def get_object(self):
        user = SingleObjectMixin.get_object(self)
        self.request.user.friends.filter(user=user).delete()
        messages.success(self.request, "Friendship removed from %s" % str(user))
        return user


# ====== TEAM VIEWS ====== #

class TeamList(ListView):
    queryset = Team.objects.exclude(enrole='S')

class TeamMixin(object):
    queryset = Team.objects.exclude(enrole='S')
    slug_url_kwarg = 'team'

class TeamDetail(TeamMixin, DetailView):
    pass

class TeamCharter(TeamDetail):
    title = _("Team Charter")
    template_name = 'person/team_charter.html'

class EditTeam(TeamMixin, UpdateView):
    form_class = TeamAdminForm

class ChatWithTeam(NeverCacheMixin, LoginRequiredMixin, TeamDetail):
    title = _("Chat")

    @property
    def template_name(self):
        if not self.request.user.has_perm('person.use_irc') \
          or 'tutorial' in self.request.GET:
            return 'chat/tutorial.html'
        return 'person/team_chat.html'

    def get(self, request, *args, **kwargs):
        if request.GET.get('irc') == 'ok':
            irc = Permission.objects.get(codename='use_irc')
            request.user.user_permissions.add(irc)
            return HttpResponseRedirect(request.path)
        return super(ChatWithTeam, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super(ChatWithTeam, self).get_context_data(**kwargs)
        data['object'] = self.get_object()
        data['page'] = int(self.request.GET.get('page', 1))
        data['chat_page'] = "chat/page-%s.svg" % data['page']
        return data


class ChatLogs(TeamDetail):
    title = _("Chatroom Logs")
    template_name = 'person/team_chatlogs.html'


class AddMember(NeverCacheMixin, LoginRequiredMixin, SingleObjectMixin, RedirectView):
    slug_url_kwarg = 'team'
    model          = Team
    permanent      = False

    def get_user(self):
        if 'username' in self.kwargs:
            return User.objects.get(username=self.kwargs['username'])
        return self.request.user

    def get_redirect_url(self, **kwargs):
        try:
            self.action(self.get_object(), self.get_user(), self.request.user)
        except (Team.DoesNotExist, User.DoesNotExist) as err:
            raise Http404(str(err))
        next_url = self.get_object().get_absolute_url()
        return self.request.GET.get('next', next_url)

    def action(self, team, user, actor=None):
        if team.enrole == 'O' or \
          (actor == team.admin and team.enrole in 'PT') or \
          (team.has_member(actor) and team.enrole == 'P'):
            if user == actor or team.has_requester(user):
                if team.has_member(user):
                    messages.error(self.request, _("You are already a member."))
                else:
                    team.update_membership(user, expired=None, joined=now(), added_by=actor)
                    messages.info(self.request, _("Team membership sucessfully added."))
            else:
                messages.error(self.request, _("This user has not requested membership."))

        elif team.enrole in 'PT' and actor == user:
            (obj, created) = team.update_membership(user, expired=None, joined=None, requested=now())
            if created:
                return messages.info(self.request, _("Membership Request Received."))
            elif obj.joined:
                return messages.info(self.request, _("You are already a member of this team."))
            else:
                return messages.info(self.request, _("You have already requested a membership to this team."))
        else:
            return messages.error(self.request, _("Can't add user to team. (not allowed)"))

class RemoveMember(AddMember):
    def action(self, team, user, actor=None):
        if actor in [user, team.admin]:
            if team.has_member(user):
                team.update_membership(user, expired=now(), removed_by=actor)
                return messages.info(self.request, _("User removed from team."))
            elif team.has_requester(user):
                team.update_membership(user, expired=now(), removed_by=actor)
                return messages.info(self.request, _("User removed from membership requests."))
            elif team.has_watcher(user):
                team.update_membership(user, expired=now(), removed_by=actor)
                return messages.info(self.request, _("User removed from watching team."))
        messages.error(self.request, _("Cannot remove user from team. (not allowed)"))

class WatchTeam(AddMember):
    def action(self, team, user, actor=None):
        if team.enrole == 'S':
            return messages.error(self.request, _("You can't watch this team."))
        team.update_membership(user, expired=None, requested=None, joined=None)
        messages.info(self.request, _("Now watching this team."))

class UnwatchTeam(AddMember):
    def action(self, team, user, actor=None):
        team.update_membership(user, expired=now(), removed_by=actor)
        messages.info(self.request, _("No longer watching this team."))

