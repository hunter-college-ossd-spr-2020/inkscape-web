#
# Copyright 2016, Martin Owens <doctormo@gmail.com>
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
"""Some core views for the inkscape website"""

__all__ = (
    'ContactOk', 'ContactUs',
    'Robots', 'SearchView', 'Authors',
)
import re
from collections import defaultdict

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.views import debug, defaults
from django.views.generic import TemplateView, FormView
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse_lazy
from django.contrib.admin.models import LogEntry
from django.shortcuts import render
from django.http import Http404

from django.conf import settings
from django.core.mail import send_mail

from haystack.forms import SearchForm
from haystack.query import SearchQuerySet
from haystack.views import SearchView as BaseView

from cms.utils import get_language_from_request

from .utils import language_alternator
from .authors import CODERS, TRANSLATORS, DOCUMENTORS
from .forms import FeedbackForm

LANG_MATCH = re.compile(r'^(?P<lang>\w{2}([_-]\w{2})?(@\w+)?)/(?P<url>.*)$')

class ContactOk(TemplateView):
    title = _('Contact Inkscape')
    template_name = 'feedback.html'

class RedirectLanguage(RedirectView):
    """Redirect any page to the given url usually prefixed /en/"""
    # Django system languages (cms, pot files etc)
    LANGS = list(dict(settings.LANGUAGES))

    @property
    def get_qset(self):
        """Append the query set to the url if it exists"""
        return '?' + self.request.GET.urlencode() if self.request.GET else ''

    def get_redirect_url(self, lang, url): # pylint: disable=arguments-differ
        """Redirect to the correct page in English"""
        url = url.rstrip('/')
        for alt in language_alternator(lang):
            if alt in self.LANGS:
                if alt == 'en':
                    return f'/{url}{self.get_qset}'
                if alt != lang:
                    return f'/{alt}/{url}{self.get_qset}'

        raise Http404("Unknown language and unknown redirect (no fallback)")

class ContactUs(FormView):
    title = _('Contact Inkscape Website Administrators')
    template_name = 'feedback.html'
    form_class = FeedbackForm

    def get_initial(self):
        ret = {'subject': self.request.GET.get('subject', "Website Feedback")}
        if self.request.user.is_authenticated():
            ret['email'] = self.request.user.email
        return ret

    def form_valid(self, form):
        recipients = ["%s <%s>" % (a,b) for (a,b) in settings.ADMINS]
        send_mail(
            form.cleaned_data['subject'],
            form.cleaned_data['comment'],
            self.get_sender(form.cleaned_data['email']), recipients)
        return super(ContactUs, self).form_valid(form) 

    def get_sender(self, email):
        if self.request.user.is_authenticated():
            user = self.request.user
            if not user.first_name:
                return email
            return '%s %s <%s>' % (user.first_name, user.last_name, email)
        if '<' not in email:
            return 'Anonymous User <%s>' % email
        return email

    def get_success_url(self):
        return reverse_lazy('contact.ok') + '?next=' + self.request.GET.get('next', '/')

class Robots(TemplateView):
    template_name = 'robots.txt'
    content_type = 'text/plain'

class SearchView(BaseView):
    """Restrict the search to the selected language only"""
    template = "search/search.html"
    searchqueryset = SearchQuerySet()
    results_per_page = 20
    form_class = SearchForm

    def __call__(self, request):
        language = get_language_from_request(request)
        self.searchqueryset = SearchQuerySet().filter(language=language)
        return super().__call__(request)

class SearchJson(SearchView):
    template = "search/search.json"

    def get_context(self):
        return {
            'query': self.query,
            'object_list': self.results[:30],
        }

    def create_response(self):
        context = self.get_context()
        return render(self.request, self.template, context, content_type="application/json")

class Authors(TemplateView):
    """Show a list of authors for the website"""
    template_name = 'authors.html'
    content_apps = \
      Q(content_type__app_label__startswith='djangocms') | \
      Q(content_type__app_label__startswith='cmsplugin') | \
      Q(content_type__app_label__in=['cmstabs', 'cms'])

    def cms_authors(self):
        """Get a list of CMS authors"""
        result = defaultdict(lambda: dict(count=0, start=3000, end=0))

        authors = LogEntry.objects.filter(self.content_apps)\
                     .values_list('user__username', 'action_time')

        for author, dt in authors:
            result[author]['name'] = author
            result[author]['email'] = None
            result[author]['count'] += 1
            if dt.year < result[author]['start']:
                result[author]['start'] = dt.year
            if dt.year > result[author]['end']:
                result[author]['end'] = dt.year
        return dict(result)

    def get_context_data(self, *args, **kwargs):
        data = super(Authors, self).get_context_data(*args, **kwargs)
        data['title'] = _('Author Credits')
        data['authors'] = [
            {'name': _('Managed Content'), 'desc': _('Licensed GPLv2 or Later and CC-BY-SA'), 'people': self.cms_authors()},
            {'name': _('Website Programmers'), 'desc': _('Licensed AGPLv3'), 'people': CODERS},
            {'name': _('Translations'), 'desc': _('Contributed to po files'), 'people': TRANSLATORS},
            {'name': _('Documentation'), 'desc': _('Contributors to Inkscape-docs team'), 'people': DOCUMENTORS},
        ]
        return data


def catch_bad_language(request, exception):
    """
    If someone asks for /xx/about we send them to the English /about page
    """
    try:
        for match in LANG_MATCH.finditer(request.path.lstrip('/')):
            return RedirectLanguage.as_view()(request, **match.groupdict())
    except Http404:
        pass
    if settings.DEBUG:
        return _original_technical_404(request, exception)
    return defaults.page_not_found(request, exception)

# Override debug 404 so we can test redirects
_original_technical_404 = debug.technical_404_response
debug.technical_404_response = catch_bad_language
