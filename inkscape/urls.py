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

from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView

from .views import ContactUs, ContactOk, SearchView, SearchJson, RedirectEnglish, Authors

urlpatterns = [ # pylint: disable=invalid-name
    url(r'^social/', include('social_django.urls', namespace='social')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)\
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)\
  + static('/dl/', document_root=settings.MEDIA_ROOT)

for e in ('403', '404', '500'):
    view = TemplateView.as_view(template_name='error/{}.html'.format(e))
    locals()['handler'+e] = view
    urlpatterns.append(url('^error/%s/$' % e, view))

if settings.ENABLE_DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

urlpatterns += i18n_patterns(
    url(r'^contact/us/$', ContactUs.as_view(), name='contact'),
    url(r'^contact/ok/$', ContactOk.as_view(), name='contact.ok'),
    url(r'^search/$', SearchView(), name='search'),
    url(r'^search/json/$', SearchJson(), name='search.json'),
    url(r'^credits/$', Authors.as_view(), name='authors'),
    url(r'^admin/lookups/', include('ajax_select.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^cog/', include('cog.urls', namespace='cog')),
    url(r'^doc/', include('docs.urls')),
    url(r'^forums/', include('forums.urls', namespace='forums')),
    url(r'^releases?/', include('releases.urls', namespace='releases')),
    url(r'^alerts/', include('alerts.urls')),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^moderation/', include('moderation.urls', namespace='moderation')),
    url(r'^news/', include('cmsplugin_news.urls', namespace='news')),
    url(r'^diff/', include('cmsplugin_diff.urls', namespace='cmsplugin_diff')),
    url(r'^~(?P<username>[^\/]+)/', include('person.user_urls')),
    url(r'^\*(?P<team>[^\/]+)/', include('person.team_urls')),
    url(r'^user/', include('person.urls')),
    url(r'^(en|da|nl|pl|sk)/(?P<url>.*)$', RedirectEnglish.as_view()),
    url(r'^', include('resources.urls')),
    # This URL is Very GREEDY, it must go last!
    url(r'^', include('cms.urls')),
    prefix_default_language=False,
)
