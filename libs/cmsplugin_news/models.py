from django.utils import timezone

from django.db.models import *
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from cms.models import CMSPlugin

from . import settings

import sys
import inspect

class LanguageNotSet(Exception):
    pass

class LanguageQuerySet(QuerySet):
    def select_language(self, lang):
        self.language = lang
        return self

    def _clone(self, *args, **kwargs):
        qs = super(LanguageQuerySet, self)._clone(*args, **kwargs)
        if hasattr(qs, 'select_language'):
            qs.select_language(self.language)
        return qs

    def iterator(self):
        if not hasattr(self, 'language'):
            raise LanguageNotSet("Can't iterate over news before the language is selected (%s)." % id(self))
        for result in super(LanguageQuerySet, self).iterator():
            yield result.select_language(self.language)


class PublishedManager(Manager):
    """This manager allows filtering of published vs not-published as well as language
       selection at display time."""
    def select_language(self, lang):
        self.language = lang
        return self

    def get_query_set(self):
        if not hasattr(self, 'language'):
            raise LanguageNotSet("Can't do a language dependant query before the language is selected.")
        return LanguageQuerySet(self.model, using=self._db).select_language(self.language)\
                .filter(is_published=True)\
                .filter(Q(language__isnull=True) | Q(language=settings.DEFAULT_LANG))


class News(Model):
    title        = CharField(_('Title'), max_length=255)
    slug         = SlugField(_('Slug'), unique_for_date='pub_date', blank=True, null=True,
                     help_text=_('A slug is a short name which uniquely identifies the news item.'))
    excerpt      = TextField(_('Excerpt'), blank=True)
    content      = TextField(_('Content'), blank=True)

    is_published = BooleanField(_('Published'), default=False)
    pub_date     = DateTimeField(_('Publication date'), default=timezone.now)

    created      = DateTimeField(auto_now_add=True, editable=False)
    updated      = DateTimeField(auto_now=True, editable=False)

    creator      = ForeignKey(User, related_name="created_news")
    editor       = ForeignKey(User, blank=True, null=True, related_name="edited_news")

    language     = CharField(_("Language"), max_length=5, choices=settings.OTHER_LANGS,
                     help_text=_("Translated version of another news item."))
    link         = URLField(_('Link'), blank=True, null=True,
                     help_text=_('This link will be used a absolute url for this item and replaces'
                                 ' the view logic. <br />Note that by default this only applies for'
                                 ' items with an empty "content" field.'))

    translation_of = ForeignKey("self", blank=True, null=True, related_name="translations")

    # django uses the first object manager for reverse lookups. Make sure normal manager is first.
    objects   = Manager()
    published = PublishedManager()

    class Meta:
        verbose_name = _('News')
        verbose_name_plural = _('News')
        ordering = ('-pub_date', )

    def __unicode__(self):
        return self.title

    def select_language(self, l):
        self._lang = l
        for item in self.get_translations():
            if item.lang == l:
                self.tr = item
        if not hasattr(self, 'tr'):
            self.tr = self
        return self

    def is_translated(self):
        return self.language != self._lang

    def __getattribute__(self, name):
        obj = self
        if name in ['title','except','editor','edited','language','content']:
            if not hasattr(self, 'tr'):
                raise LanguageNotSet("Language is required to be set to access data like this.")
            obj = self.tr
        if name == 'lang':
            name = 'language'
        return Model.__getattribute__(obj, name)

    def get_translations(self):
        if self.is_published:
            return self.translations.filter(is_published=True)
        return self.translations.all()

    def get_absolute_url(self):
        if settings.LINK_AS_ABSOLUTE_URL and self.link:
            if settings.USE_LINK_ON_EMPTY_CONTENT_ONLY and not self.content:
                return self.link
        if self.is_published:
            return reverse('news_detail', kwargs={
                'year'  : self.pub_date.strftime("%Y"),
                'month' : self.pub_date.strftime("%m"),
                'day'   : self.pub_date.strftime("%d"),
                'slug'  : self.slug})
        return reverse('news_item', kwargs={ 'news_id': self.id })


class LatestNewsPlugin(CMSPlugin):
    """
        Model for the settings when using the latest news cms plugin
    """
    limit = PositiveIntegerField(_('Number of news items to show'),
                    help_text=_('Limits the number of items that will be displayed'))


