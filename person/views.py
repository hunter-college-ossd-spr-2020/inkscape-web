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
"""Customise the user authentication model"""


from django.views.generic import (
    UpdateView, DetailView, ListView, RedirectView, TemplateView, View
)
from django.template.response import TemplateResponse
from django.views.generic.detail import SingleObjectMixin
from django.utils.translation import ugettext_lazy as _, get_language
from django.utils.timezone import now
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.auth.views import LoginView as BaseLoginView
from django.http import HttpResponseRedirect, Http404
from django.urls import translate_url

from django_registration.backends.activation.views import RegistrationView

from .models import User, Team, TeamMembership
from .forms import UserForm, AgreeToClaForm
from .team_forms import TeamAdminForm
from .mixins import LoginRequiredMixin, NeverCacheMixin, UserMixin, NextUrlMixin

class LoginView(BaseLoginView):
    def get_success_url(self):
        url = super().get_success_url()
        lang = self.request.user.language or get_language()
        return translate_url(url, lang)

class AgreeToCla(NeverCacheMixin, NextUrlMixin, UserMixin, UpdateView):
    template_name = 'person/cla-agree.html'
    title = _('Contributors License Agreement')
    form_class = AgreeToClaForm

class EmailChangedView(RegistrationView):
    email_body_template = 'django_registration/reactivation_email_body.txt'
    email_subject_template = 'django_registration/reactivation_email_subject.txt'


class EditProfile(NeverCacheMixin, NextUrlMixin, UserMixin, UpdateView):
    title = _('Edit User Profile')
    form_class = UserForm

    def form_valid(self, form):
        new_email = form.cleaned_data.get('email')
        old_email = User.objects.get(pk=self.object.pk).email
        # Save data before checking email
        ret = super().form_valid(form)
        if new_email != old_email:
            self.email_changed(form.instance, old_email, new_email)
        return ret

    def email_changed(self, instance, old_email, new_email):
        """
        The email address was changed, so reset the active flag and email them.
        """
        # We update the last_login on email change to prevent change
        # password attacks which would allow an attacker re-access to
        # an account. Changing the date here will invalidate any hash.
        #instance.last_login = now()
        self.request.session.flush()
        # Deactivate account and send new confirmation email
        instance.is_active = False
        instance.save()

        # send email activation
        fake_registration = EmailChangedView(request=self.request)
        fake_registration.send_activation_email(instance)

        messages.warning(self.request,\
            _("Your email address has changed, we have sent a new confirmation email. "
              "Please confirm your new email address to log back in."))

        # Send notification email to old email address just in case it's not authorised.
        send_mail(
            _("Email Address Changed"),
            _("Your email address on inkscape.org has changed from %s to %s, "
              "if this is incorrect, please email the webmaster for assistance."
             ) % (old_email, new_email),
            "Inkscape Webmaster <webmaster@inkscape.org>",
            [old_email])


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
    template_name = 'django_registration/welcome.html'
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

class EditTeam(LoginRequiredMixin, TeamMixin, UpdateView):
    form_class = TeamAdminForm

    def is_allowed(self, user):
        return user == self.get_object().admin


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

class MembershipRequestView(NeverCacheMixin, LoginRequiredMixin, DetailView):
    """
    View a membership request, with the ability to comment on them.
    """
    model = TeamMembership

    def is_allowed(self, user):
        """Can the user access this request view"""
        obj = self.get_object()
        return obj.user == user \
            or obj.team.admin == user \
            or user.is_superuser

    def get_object(self, queryset=None):
        """The object is based on the user currently logged in"""
        if 'pk' not in self.kwargs:
            team = Team.objects.get(slug=self.kwargs['team'])
            try:
                return team.memberships.get(user=self.request.user)
            except TeamMembership.DoesNotExist:
                raise Http404()
        # Primary Key lookup is used for admins to see requests
        return super().get_object(queryset=queryset)

class AddMember(NeverCacheMixin, LoginRequiredMixin, SingleObjectMixin, RedirectView):
    """
    Add a user to a team, this membership may not be complete after this action and
    may need peer or administration approval.
    """
    slug_url_kwarg = 'team'
    permanent = False
    model = Team

    def get_user(self):
        if 'username' in self.kwargs:
            return User.objects.get(username=self.kwargs['username'])
        return self.request.user

    def get_redirect_url(self, **kwargs):
        try:
            next_url = self.action(self.get_object(), self.get_user(), self.request.user)
        except (Team.DoesNotExist, User.DoesNotExist) as err:
            raise Http404(str(err))
        return self.request.GET.get('next', next_url)

    def action(self, team, user, actor=None):
        """Action of this joining request"""
        if not user.email:
            messages.error(self.request, _("User must have an email address set in their profile to get membership to a team."))
        elif team.enrole == 'O' or \
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
            (obj, created) = team.update_membership(
                user, expired=None, joined=None, requested=now())
            if created:
                messages.info(self.request, _("Membership Request Received."))
            elif obj.joined:
                messages.info(self.request, _("You are already a member of this team."))
            else:
                messages.info(self.request, _("Already requested a membership to this team."))
            return obj.get_absolute_url(for_user=user)
        else:
            messages.error(self.request, _("Can't add user to team. (not allowed)"))
        return team.get_absolute_url()

class RemoveMember(AddMember):
    """
    Remove member request, watching or membership itself.
    """
    def action(self, team, user, actor=None):
        """Action which is called by AddMember.get_redirect_url"""
        if actor in [user, team.admin]:
            if team.has_member(user):
                team.update_membership(user, expired=now(), removed_by=actor)
                messages.info(self.request, _("User removed from team."))
            elif team.has_requester(user):
                team.update_membership(user, expired=now(), removed_by=actor)
                messages.info(self.request, _("User removed from membership requests."))
            elif team.has_watcher(user):
                team.update_membership(user, expired=now(), removed_by=actor)
                messages.info(self.request, _("User removed from watching team."))
            else:
                messages.error(self.request, _("Cannot remove user from team. (not allowed)"))
        else:
            messages.error(self.request, _("Cannot remove user from team. (not allowed)"))
        return team.get_absolute_url()

class WatchTeam(AddMember):
    """
    Add a membership which is only concerned with watching the team.
    """
    def action(self, team, user, actor=None):
        """Action which is called by AddMember.get_redirect_url"""
        if team.enrole == 'S':
            messages.error(self.request, _("You can't watch this team."))
        else:
            team.update_membership(user, expired=None, requested=None, joined=None)
            messages.info(self.request, _("Now watching this team."))
        return team.get_absolute_url()

class UnwatchTeam(AddMember):
    """
    Remove a watching membership specifically.
    """
    def action(self, team, user, actor=None):
        """Action which is called by AddMember.get_redirect_url"""
        team.update_membership(user, expired=now(), removed_by=actor)
        messages.info(self.request, _("No longer watching this team."))
        return team.get_absolute_url()

class UserAvatar(View):
    """
    Attempts to find a user's avatar by their IRC nickname or website username.
    """
    permanent = True
    skip_middleware = True

    def get_object(self, nick):
        """Get the nearest matching user with this nickname"""
        user = User.objects.filter(ircnick=nick).order_by('pk').first()
        if user is None:
            user = User.objects.filter(username=nick).order_by('pk').first()
        return user, nick

    def get(self, request, nick, ext=None):
        """Redirect to the given picture file."""
        from django.http import HttpResponse
        from resources.utils import FileEx

        user, nick = self.get_object(nick)
        if user is None or not user.photo:
            return self.generate_svg(nick)
        user.photo.open()
        fex = FileEx(user.photo.path)
        return HttpResponse(user.photo.read(), content_type=str(fex.mime))

    @staticmethod
    def string_to_colour(string):
        """Convert a string into a colour for use in a generated avatar"""
        total = 0

        for char in string:
            total = ord(char) + ((total << 5) - total)

        return '#' + ''.join(['{:02x}'.format((total >> (i * 8)) & 0xFF) for i in range(3)])

    def generate_svg(self, nick):
        """Return a generated svg based on a template"""
        return TemplateResponse(
            self.request,
            template='person/irc_avatar.svg',
            context={'nick': nick, 'colour': self.string_to_colour(nick)},
            content_type='image/svg+xml')
