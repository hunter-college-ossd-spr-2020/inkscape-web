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
try:
    from django.conf.urls import patterns, url, include
except ImportError:
    from django.conf.urls.defaults import patterns, url, include

from .views import *
from person.urls import USER_URLS

urlpatterns = patterns('',
  url(r'^$',                         ProjectList(),     name="project.list"),
  url(r'^gsoc/$',                    ProjectGsocList(), name="project.gsoc.list"),

  url(r'^new/$',                     NewProject(),      name="project.new"),
  url(r'^(?P<slug>[\w-]+)/update/$', UpdateProject(),   name="project.update"),
  url(r'^(?P<slug>[\w-]+)/$',        ProjectView(),     name="project.view"),
)

USER_URLS.url_patterns.extend([
  url(r'^/myprojects/$',             MyProjects(),      name="my_projects"),
])
