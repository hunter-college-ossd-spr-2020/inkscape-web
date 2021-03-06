#
# Copyright 2015-2018, Martin Owens <doctormo@gmail.com>
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
"""Models for website news"""

from django.db.models import Model, Manager,\
    CharField, TextField, SlugField, BooleanField, DateTimeField, ForeignKey,\
    ImageField, URLField, PositiveIntegerField
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import timezone

from cms.models import CMSPlugin
from cms.utils.permissions import get_current_user as get_user

from .settings import OTHER_LANGS, DEFAULT_LANG, \
    LINK_AS_ABSOLUTE_URL, USE_LINK_ON_EMPTY_CONTENT_ONLY

class LanguageNotSet(Exception):
    pass


class PublishedManager(Manager):
    """This manager allows filtering of published vs not-published as well as language
       selection at display time."""
    def select_language(self, lang):
        """Select the language (set attribute)"""
        self.language = lang
        return self

    def with_language(self, lang, **kwargs):
        """Returns the news queryset with a given language"""
        return self.select_language(lang).get_queryset(**kwargs)

    def get_queryset(self, is_staff=False):
        """Return the queryset for published news"""
        if not hasattr(self, 'language'):
            raise LanguageNotSet("Can't do a language dependant query before"
                                 " the language is selected.")

        qset = super(PublishedManager, self).get_queryset()
        english = qset.filter(translation_of__isnull=True)

        if self.language == 'en':
            qset = english
        else:
            untranslated = english.exclude(translations__language=self.language)
            qset = untranslated | qset.filter(language=self.language)
        if not is_staff:
            qset = qset.filter(is_published=True, pub_date__lte=timezone.now())
        return qset


class News(Model):
    title = CharField(_('Title'), max_length=255)
    slug = SlugField(_('Slug'), unique_for_date='pub_date', null=True,\
           help_text=_('A slug is a short name which provides a unique url.'))

    excerpt = TextField(_('Excerpt'), blank=True)
    content = TextField(_('Content'), blank=True)

    is_published = BooleanField(_('Published'), default=False)
    pub_date = DateTimeField(_('Publication date'), default=timezone.now)
    group = ForeignKey(Group, null=True, blank=True,\
        help_text=_('News group indicates that this news is exclusive to '\
          'this group only. This usually means it won\'t be visible on '\
          'the main news listings, but instead is listed elsewhere.'))

    created = DateTimeField(auto_now_add=True, editable=False)
    updated = DateTimeField(auto_now=True, editable=False)

    creator = ForeignKey(settings.AUTH_USER_MODEL, related_name="created_news", default=get_user)
    editor = ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name="edited_news")

    link = URLField(_('Link'), blank=True, null=True,\
         help_text=_('This link will be used as absolute url for this item '\
         'and replaces the view logic. <br />Note that by default this '\
         'only applies for items with an empty "content" field.'))

    # The translation functionality could be brought into a more generic format
    # By making a meta class which doesn't have its own table but contains
    # these two fields and specifying 1. a list of translated fields which
    # __getattr always passes UP to the translated version and 2. a list of
    # base fields which __getattr always passes DOWN to the root.
    # All mechanisms to do with translations would then be brought into
    # that generic class.
    language = CharField(_("Language"), max_length=8, choices=OTHER_LANGS,\
        db_index=True, help_text=_("Translated version of another news item."))
    translation_of = ForeignKey("self", blank=True, null=True, related_name="translations")

    # django uses the first object manager for reverse lookups.
    # Make sure normal manager is first.
    objects = Manager()
    published = PublishedManager()

    tr_fields = ['translated', 'title', 'excerpt', 'language', 'content']

    class Meta:
        verbose_name = _('News')
        verbose_name_plural = _('News')
        ordering = ('-pub_date', )
        permissions = (
            ('translate_news', _('Translate News')),
        )

    @property
    def lang(self):
        return self.language or 'en'

    def __str__(self):
        return self.title

    def select_language(self, lang):
        """Returns the translation for this news"""
        self._lang = lang.split('-')[0]
        self.trans = self.get_translation(lang) or self
        return self

    def __getattribute__(self, name):
        obj = self
        if name in News.tr_fields and hasattr(obj, 'trans'):
            obj = self.trans
        elif name == 'translated':
            name = 'updated'
        return Model.__getattribute__(obj, name)

    def get_translations(self):
        if self.translation_of:
            return self.translation_of.get_translations()
        return self.translations.all()

    def get_translation(self, lang):
        try:
            return self.get_translations().get(language=lang)
        except News.DoesNotExist:
            return None

    def needs_translation(self):
        return not self.is_original() and (self.trans == self or self.trans.updated < self.updated)

    def is_original(self):
        return not hasattr(self, '_lang') or self._lang == DEFAULT_LANG

    def save(self, **kw):
        """Keep translations fields up to date with master english version"""
        if self.translation_of:
            self.is_published = self.translation_of.is_published
            self.pub_date = self.translation_of.pub_date
        else:
            self.translations.update(
              is_published=self.is_published,
              pub_date=self.pub_date)
        return super(News, self).save(**kw)

    @classmethod
    def get_list_url(cls):
        return reverse('news:archive_index')

    def get_absolute_url(self):
        if LINK_AS_ABSOLUTE_URL and self.link:
            if USE_LINK_ON_EMPTY_CONTENT_ONLY and not self.content:
                return self.link
        if self.is_published and self.slug:
            return reverse('news:detail', kwargs={
                'year'  : self.pub_date.strftime("%Y"),
                'month' : self.pub_date.strftime("%m"),
                'day'   : self.pub_date.strftime("%d"),
                'slug'  : self.slug})
        return reverse('news:item', kwargs={'pk': self.pk})


class SocialMediaType(Model):
    """
    A place online where this news was shared.
    """
    name = CharField(max_length=255)
    icon = ImageField(upload_to='news/icons')

    def __str__(self):
        return self.name


class NewsBacklink(Model):
    """
    How this news was shared with the world.
    """
    news = ForeignKey(News, related_name='backlinks')
    url = URLField()
    social_media = ForeignKey(SocialMediaType, null=True, blank=True)
    delibrate = BooleanField(default=True,
        help_text=_('Was this post done by a known contributor?'))

    def __str__(self):
        return self.url


class LatestNewsPlugin(CMSPlugin):
    """
        Model for the settings when using the latest news cms plugin
    """
    limit = PositiveIntegerField(_('Number of news items to show'),
                    help_text=_('Limits the number of items that will be displayed'))
    group = ForeignKey(Group, blank=True, null=True,
        help_text=_('Limit this news plugin to this group only. If set to '
          ' "None" then this plugin will only show news with NO group.'))



