# -*- coding: utf-8 -*-
#
# Copyright 2017, Martin Owens <doctormo@gmail.com>
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
Election views, showing different pages in the election system.
"""

from django.views.generic import DetailView, ListView, UpdateView, RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import Http404
from django.db.models import Q
from django.db.utils import IntegrityError

from person.models import Team

from .models import Election, Ballot, Candidate
from .mixins import TeamMemberMixin

class ElectionList(ListView):
    model = Election

class ElectionDetail(DetailView):
    model = Election

    def get_context_data(self, **kw):
        data = super(ElectionDetail, self).get_context_data(**kw)
        data['invitation'] = data['object']._candidates.\
            filter(invitor_id=self.request.user.id).first()
        data['ballot'] = data['object'].ballots.\
            filter(user_id=self.request.user.id).first()
        data['candidates'] = list(self.candidates(data['ballot']))

        if 'q' in self.request.GET:
            q = self.request.GET['q']
            name_query = Q(first_name__iexact=q) | Q(last_name__iexact=q)
            if ' ' in q:
                (first, last) = q.split(' ', 1)
                name_query = Q(first_name__iexact=first) & Q(last_name__iexact=last)

            qs = get_user_model().objects.filter(
                Q(username__iexact=q) | Q(email__iexact=q) | name_query
            )
            data['search_count'] = qs.count()
            qs = qs[:50]
            data['search'] =  qs
        return data

    def candidates(self, ballot):
        if ballot and ballot.responded:
            # Return candidates in voting order based on previous ballot.
            for item in ballot.votes.all():
                yield (item.candidate, item)
        else:
            for item in self.get_object().candidates.order_by('?'):
                yield (item, None)


class ElectionVote(TeamMemberMixin, SingleObjectMixin, RedirectView):
    permanent = False
    model = Election

    def post(self, request, **kw):
        ballot = get_object_or_404(Ballot, slug=kw['hash'])
        has_vote = False
        # We MUST delete the votes, because re-ordering can cause
        # the unique database checks to flag as we re-save the new
        # posissions. Do not change to update_or_create pattern.
        ballot.votes.all().delete()
        for key, value in request.POST.items():
            if key.startswith('vote_'):
                try:
                    value = int(value)
                    has_vote = True
                except ValueError:
                    value = None
                ballot.votes.create(candidate_id=key[5:], rank=value)

        ballot.responded = has_vote
        ballot.save()
        if has_vote:
            messages.success(self.request, _('Your ballot has been saved'))
        else:
            messages.warning(self.request, _('Your votes have been cleared'))
        return self.get(request, **kw)

    def get_redirect_url(self, **kw):
        next_url = self.get_object().get_absolute_url()
        return self.request.GET.get('next', next_url)


class ElectionInvite(TeamMemberMixin, SingleObjectMixin, RedirectView):
    permanent = False
    model = Election

    def get_redirect_url(self, **kwargs):
        User = get_user_model()
        try:
            election = self.get_object()
            user = User.objects.get(pk=kwargs['user_id'])
            Candidate.objects.create(election=election, user=user,
                invitor=self.request.user)
            messages.success(self.request, _('Invitation sent'))
        except (Election.DoesNotExist, User.DoesNotExist) as err:
            raise Http404(str(err))
        except IntegrityError:
            messages.error(self.request, _('This person is already invited'))

        next_url = self.get_object().get_absolute_url()
        return self.request.GET.get('next', next_url)

class ElectionInviteMessage(TeamMemberMixin, DetailView):
    template_name = 'elections/alert/email_candidate_invitation_alert.txt'
    content_type = 'text/plain'
    model = Election

    def get_context_data(self, **kw):
        data = super(ElectionInviteMessage, self).get_context_data(**kw)
        user = get_user_model().objects.get(pk=self.kwargs['user_id'])
        data['instance'] = {'election': self.get_object()}
        data['alert'] =  {'user': user}
        return data


class ElectionAccept(SingleObjectMixin, RedirectView):
    slug_url_kwarg = 'hash'
    permanent = False
    accepted = True

    def get_redirect_url(self, **kwargs):
        obj = self.get_object()
        obj.responded = True
        obj.accepted = self.accepted
        obj.save()

        if self.accepted:
            messages.success(self.request, _('Invitation Accepted'))
        else:
            messages.error(self.request, _('Invitation NOT Accepted'))

        return self.request.GET.get('next', obj.election.get_absolute_url())

    def get_queryset(self):
        return Candidate.objects.filter(election__slug=self.kwargs['slug'])
  
