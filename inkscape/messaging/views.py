# -*- coding: utf-8 -*-
#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.urlresolvers import reverse

from pile.views import CreateView, CategoryListView
from .models import User, UserAlert, Message

class AlertList(CategoryListView):
    model = UserAlert
    opts = (
      ('alerttype', 'alert__slug'),
      ('new', 'viewed__isnull'),
    )

    def get_queryset(self, **kwargs):
        queryset = super(AlertList, self).get_queryset(**kwargs)
        return queryset.filter(user=self.request.user)

    def get_context_data(self, **data):
        data = super(AlertList, self).get_context_data(**data)
        if data['alerttype'] and isinstance(data['alerttype'], (tuple, list)):
            data['alerttype'] = data['alerttype'][0]
        return data


@login_required
def mark_viewed(request, alert_id):
    alert = get_object_or_404(UserAlert, pk=alert_id, user=request.user)
    alert.view()
    return HttpResponse(alert.pk)


@login_required
def mark_deleted(request, alert_id):
    alert = get_object_or_404(UserAlert, pk=alert_id, user=request.user)
    alert.delete()
    return HttpResponse(alert.pk)


class CreateMessage(CreateView):
    model = Message
    fields = ('subject','body','recipient','reply_to')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.sender = self.request.user
        obj.reply_to = self.get_reply_to()
        obj.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('my_profile')

    def get_reply_to(self):
        msg = self.gost('reply_to', None)
        if msg:
            # If we ever want to restrict who can reply, do it here first.
            msg = get_object_or_404(Message, pk=msg, recipient=self.request.user)
        return msg

    def get_initial(self):
        """Add reply to subject initial data"""
        initial = super(CreateMessage, self).get_initial()
        rto = self.get_reply_to()
        if rto:
            initial['subject'] = (rto.reply_to and "Re: " or "") + rto.subject
            self.recipient = rto.sender
        else:
            self.recipient = get_object_or_404(User, pk=int(self.gost('recipient', 0)))
        initial['recipient'] = self.recipient.pk
        return initial

    def get_context_data(self, **data):
        """Add reply to message object to template output"""
        data = super(CreateMessage, self).get_context_data(**data)
        data['reply_to'] = self.get_reply_to()
        data['recipient'] = self.recipient
        return data

