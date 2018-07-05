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
"""Views for both user and group actions and views"""

from registration.backends.default.views import ActivationView as AV, RegistrationView
from django.conf.urls import url, include
from django.views.generic.base import TemplateView
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordResetView as Reset, PasswordResetConfirmView as Confirm,
    PasswordResetCompleteView as Complete, PasswordResetDoneView as ResetDone,
)
from alerts.views import CreateMessage
from inkscape.url_utils import url_tree

from .views import (
    UserDetail, EditProfile, UserGPGKey, MakeFriend, LeaveFriend, TeamDetail,
    AddMember, RemoveMember, WatchTeam, UnwatchTeam, ChatLogs, TeamCharter,
    EditTeam, TeamList, ChatWithTeam, MyProfile, AgreeToCla, Welcome
)
from .forms import RegisForm, PasswordForm

AC = TemplateView.as_view(template_name='registration/activation_complete.html')
RC = TemplateView.as_view(template_name='registration/registration_complete.html')
RK = TemplateView.as_view(template_name='registration/registration_closed.html')
RG = RegistrationView.as_view(form_class=RegisForm)
PWDCONFIRM = r'^(?P<uidb64>[0-9A-Za-z_\-]+?)/(?P<token>.+)/$'

# Our user url implementation allows other urls files to add
# their own urls to our user tree. Creating user functions.
USER_URLS = url_tree(
    r'^~(?P<username>[^\/]+)/',
    url(r'^$', UserDetail.as_view(), name='view_profile'),
    url(r'^gpg/$', UserGPGKey.as_view(), name='user_gpgkey'),
    url(r'^friend/$', MakeFriend.as_view(), name='user_friend'),
    url(r'^unfriend/$', LeaveFriend.as_view(), name='user_unfriend'),
    # Example message system
    url(r'^message/$', CreateMessage.as_view(), name="message.new"),
    url(r'^message/(?P<pk>\d+)/$', CreateMessage.as_view(), name="message.reply"),
)
TEAM_URLS = url_tree(
    r'^\*(?P<team>[^\/]+)/',
    url(r'^$', TeamDetail.as_view(), name='team'),
    url(r'^edit/$', EditTeam.as_view(), name='team.edit'),
    url(r'^join/$', AddMember.as_view(), name='team.join'),
    url(r'^watch/$', WatchTeam.as_view(), name='team.watch'),
    url(r'^leave/$', RemoveMember.as_view(), name='team.leave'),
    url(r'^unwatch/$', UnwatchTeam.as_view(), name='team.unwatch'),
    url(r'^charter/$', TeamCharter.as_view(), name='team.charter'),
    url(r'^elections/', include('elections.urls', namespace='elections')),

    url(r'^chat/$', ChatWithTeam.as_view(), name='team.chat'),
    url(r'^chat/logs/$', ChatLogs.as_view(), name='team.chatlogs'),
    url_tree(
        r'^(?P<username>[^\/]+)/',
        url(r'^approve/$', AddMember.as_view(), name='team.approve'),
        url(r'^remove/$', RemoveMember.as_view(), name='team.remove'),
        url(r'^disapprove/$', RemoveMember.as_view(), name='team.disapprove'),
    ),
)

urlpatterns = [ # pylint: disable=invalid-name
    url_tree(
        r'^user/',
        url(r'^$', MyProfile.as_view(), name='my_profile'),
        url(r'^cla/$', AgreeToCla.as_view(), name='agree_to_cla'),
        url(r'^edit/$', EditProfile.as_view(), name='edit_profile'),
        url(r'^welcome/$', Welcome.as_view(), name='welcome'),
        url(r'^login/', LoginView.as_view(), name='auth_login'),
        url(r'^logout/', LogoutView, name='auth_logout'),
        url_tree(
            r'^pwd/',
            url(r'^$', Reset.as_view(form_class=PasswordForm), name='password_reset'),
            url(PWDCONFIRM, Confirm.as_view(), name='password_reset_confirm'),
            url(r'^done/$', Complete.as_view(), name='password_reset_complete'),
            url(r'^sent/$', ResetDone.as_view(), name='password_reset_done'),
        ),

        url_tree(
            r'^register/',
            url(r'^$', RG, name='auth_register'),
            url(r'^closed/$', RK, name='registration_disallowed'),
            url(r'^complete/$', RC, name='registration_complete'),
            url(r'^activate/(?P<activation_key>\w+)/$', AV.as_view(), name='registration_activate'),
            url(r'^activated/$', AC, name='registration_activation_complete'),
        ),
    ),
    url(r'^teams/$', TeamList.as_view(), name='teams'),
    USER_URLS,
    TEAM_URLS,
]
