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
"""Main website urls, from here all other things sprong"""

from django.urls import path
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.contrib import admin

from .views import ContactUs, ContactOk, SearchView, SearchJson, RedirectEnglish, Authors

urlpatterns = [ # pylint: disable=invalid-name
    path('social/', include('social_django.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)\
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)\
  + static('/dl/', document_root=settings.MEDIA_ROOT)

#if settings.ENABLE_DEBUG_TOOLBAR:
#    import debug_toolbar
#    urlpatterns.append(
#        url(r'^__debug__/', include(debug_toolbar.urls)),
#    )

urlpatterns += [
    path('contact/us/', ContactUs.as_view(), name='contact'),
    path('contact/ok/', ContactOk.as_view(), name='contact.ok'),
    path('search/', SearchView(), name='search'),
    path('search/json/', SearchJson(), name='search.json'),
    path('credits/', Authors.as_view(), name='authors'),
    path('admin/', admin.site.urls),

    # Docs app
    path('doc/', include('docs.urls')),
    url(r'^(?P<lang>[\w\-\_]{2,10})/doc/', include('docs.urls')),

    path('forums/', include('forums.urls')),
    #url(r'^releases?/', include('releases.urls')),
    path('alerts/', include('alerts.urls')),
    path('comments/', include('django_comments.urls')),
    #path('moderation/', include('moderation.urls')),
    path('news/', include('news.urls')),

    # User related urls
    url(r'^~(?P<username>[^\/]+)/', include('person.user_urls')),
    url(r'^\*(?P<team>[^\/]+)/', include('person.team_urls')),
    url(r'^user/', include('person.urls')),

    # Redirection urls
    url(r'^(en|da|nl|pl|sk)/(?P<url>.*)$', RedirectEnglish.as_view()),
    path('', include('resources.urls')),
]
