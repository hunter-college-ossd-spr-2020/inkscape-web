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
"""
News views (non-staff views)
"""

from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView, DateDetailView, \
        YearArchiveView, MonthArchiveView, DayArchiveView

from django.http import Http404, HttpResponseRedirect
from django.utils import translation
from django.shortcuts import get_object_or_404

from .models import News
from .mixins import PublishedNewsMixin
from .settings import ARCHIVE_PAGE_SIZE

class DetailNews(PublishedNewsMixin, DetailView):
    """
    A primary key based news article lookup.
    """
    model = News

    def get_object(self):
        qs = self.get_queryset()
        try:
            return qs.get(pk=self.kwargs['pk'])
        except News.DoesNotExist:
            obj = get_object_or_404(News, pk=self.kwargs['pk'])
            try:
                return obj.translations.get(language=self.get_language())
            except News.DoesNotExist:
                return obj


class ArchiveIndexView(PublishedNewsMixin, ListView):
    """
    A simple archive view that exposes following context:

    * latest
    * date_list
    * paginator
    * page_obj
    * object_list
    * is_paginated

    The first two are intended to mimic the behaviour of the
    date_based.archive_index view while the latter ones are provided by
    ListView.
    """
    paginate_by = ARCHIVE_PAGE_SIZE
    template_name = 'cmsplugin_news/news_archive.html'
    include_yearlist = True
    title = _("Latest News")

    def get_context_data(self, **kwargs):
        context = super(ArchiveIndexView, self).get_context_data(**kwargs)
        context['latest'] = context['object_list']
        if self.include_yearlist:
            date_list = self.get_queryset().datetimes('pub_date', 'year')[::-1]
            context['date_list'] = date_list
        return context


class DetailView(PublishedNewsMixin, DateDetailView):
    template_name = 'cmsplugin_news/news_detail.html'
    allow_future = True

    def get(self, request, *args, **kwargs):
        try:
            return super(DetailView, self).get(request, *args, **kwargs)
        except Http404:
            # Do a lookup for this slug and redirect if possible
            for obj in News.objects.filter(slug=kwargs['slug']):
                # Does translation already exists?
                item = obj.get_translation(translation.get_language())
                if item is None:
                    # Translation doesn't exist, so go somewhere useful.
                    if obj.translation_of:
                        item = obj.translation_of
                    else:
                        item = obj
                    item.language = translation.get_language()
                with translation.override(item.language or 'en'):
                    url = item.get_absolute_url()
                    if url != request.path:
                        return HttpResponseRedirect(url)
            raise


class YearArchiveView(PublishedNewsMixin, YearArchiveView):
    template_name = 'cmsplugin_news/news_archive_year.html'
    make_object_list = True

class MonthArchiveView(PublishedNewsMixin, MonthArchiveView):
    template_name = 'cmsplugin_news/news_archive_month.html'

class DayArchiveView(PublishedNewsMixin, DayArchiveView):
    template_name = 'cmsplugin_news/news_archive_day.html'

