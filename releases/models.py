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
Record and control releases.
"""

import os
from collections import defaultdict

from django.db.models import (
    Model, SlugField, CharField, TextField, ForeignKey,
    BooleanField, IntegerField, PositiveIntegerField,
    DateField, DateTimeField, URLField,
    QuerySet, Q
)
from django.conf import settings

from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from django.core.cache import caches
from django.core.urlresolvers import reverse

from inkscape.fields import ResizedImageField
from inkscape.templatetags.i18n_fields import OTHER_LANGS, translate_field

null = dict(null=True, blank=True) # pylint: disable=invalid-name
User = settings.AUTH_USER_MODEL # pylint: disable=invalid-name

CACHE = caches['default']

def upload_to(name, width=960, height=300):
    """Quick upload for releases"""
    return dict(null=True, blank=True,
                upload_to=os.path.join('release', name),
                max_height=height, max_width=width)


class ReleaseStatus(Model):
    """For non-released (finalised) Releases, what stage are we at"""
    STYLES = (
        ('blue', _('Blue')),
    )
    name = CharField(max_length=32)
    desc = CharField(_('Description'), max_length=128)
    style = CharField(max_length=32, choices=STYLES, **null)
    icon = ResizedImageField(**upload_to('icons', 32, 32))

    class Meta:
        verbose_name_plural = 'Release Statuses'

    def __str__(self):
        return self.name


class Project(Model):
    """A project such as Inkscape which has releases"""
    slug = SlugField(max_length=128, primary_key=True)
    name = CharField(max_length=128)
    default = BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('releases:download') + '?project=' + self.slug


class ReleaseQuerySet(QuerySet):
    """Release breadcrumb crontrols"""
    breadcrumb_name = lambda self: _("Releases")
    get_absolute_url = lambda self: reverse('releases:download')

    def for_parent(self, parent):
        """Get all items that have no parent or are children of the given parent"""
        pkey = parent.parent_id if parent.parent_id else parent.pk
        qset = self.filter(Q(parent__isnull=True) | Q(parent_id=pkey))
        return qset.filter(project_id=parent.project_id)


class Release(Model):
    """A release of inkscape"""
    project = ForeignKey(Project, related_name='releases', **null)
    parent = ForeignKey('self', related_name='children', **null)
    version = CharField(_('Version'), max_length=16, db_index=True)
    version_name = CharField(_('Version Name'), max_length=64, null=True, blank=True,\
        help_text=_("If set, uses this string for the version in the display."))
    is_prerelease = BooleanField(_('is Pre-Release'), default=False, \
        help_text=_("If set, will indicate that this is a testing "
                    "pre-release and should not be given to users."))
    is_draft = BooleanField(default=False,\
        help_text=_("Set to true if this release should not be visible at all in the front end."))
    html_desc = CharField(_('HTML Description'), max_length=255, **null)
    keywords = CharField(_('HTML Keywords'), max_length=255, **null)

    release_notes = TextField(_('Release notes'), **null)
    release_date = DateField(_('Release date'), db_index=True, \
        help_text=_("ONLY set this when THIS release is ready to go. Set "
                    "pre-release dates on pre-releases and remember, as s"
                    "oon as this is released, it will take over the defau"
                    "lt redirection and users will start downloading this"
                    " release."), **null)
    status = ForeignKey(ReleaseStatus, \
        help_text=_("When release isn't finalised, document if we are in f"
                    "reezing, etc, useful for development."), **null)

    edited = DateTimeField(_('Last edited'), auto_now=True)
    created = DateTimeField(_('Date created'), auto_now_add=True, db_index=True)
    background = ResizedImageField(**upload_to('background', 960, 360))

    manager = ForeignKey(User, verbose_name=_("Manager"), related_name='releases', \
        help_text=_("Looks after the release schedule and release meetings."), **null)
    reviewer = ForeignKey(User, verbose_name=_("Reviewer"), related_name='rev_releases', \
        help_text=_("Reviewers help to make sure the release is working."), **null)
    bug_manager = ForeignKey(User, verbose_name=_("Bug Manager"), related_name='bug_releases', \
        help_text=_("Manages critical bugs and decides what needs fixing."), **null)
    translation_manager = ForeignKey(User, verbose_name=_("Translation Manager"), \
        help_text=_("Translation managers look after all translations for the release."), \
        related_name='tr_releases', **null)

    objects = ReleaseQuerySet.as_manager()

    class Meta:
        ordering = ('-release_date',)
        get_latest_by = 'release_date'
        unique_together = ('project', 'version')

    def __str__(self):
        if self.project:
            return "{} {}".format(self.project.name, self.get_version_name())
        return self.get_version_name()

    def get_version_name(self):
        return self.version_name or self.version

    def get_absolute_url(self):
        """Return a specific url for this release"""
        kwargs = {'version': self.version}
        if self.project_id:
            kwargs['project'] = self.project_id
        return reverse('releases:release', kwargs=kwargs)

    def breadcrumb_parent(self):
        return self.parent if self.parent else Release.objects.all()

    @property
    def revisions(self):
        return Release.objects.filter(Q(parent_id=self.pk) | Q(id=self.pk)).filter(is_draft=False)

    @property
    def latest(self):
        qset = self.revisions.filter(platforms__isnull=False)
        if qset.count() > 0:
            return qset.order_by('-release_date')[0]
        return None

    def responsible_people(self):
        """Quick list of all responsible people with labels"""
        for key in ('manager', 'reviewer', 'translation_manager', 'bug_manager'):
            yield (getattr(Release, key).field.verbose_name,
                   getattr(Release, key).field.help_text,
                   getattr(self, key))


class ReleaseTranslation(Model):
    """A translation of a Release"""
    release = ForeignKey(Release, related_name='translations')
    language = CharField(_("Language"), max_length=8, choices=OTHER_LANGS, db_index=True,
                         help_text=_("Which language is this translated into."))

    html_desc = CharField(_('HTML Description'), max_length=255, **null)
    keywords = CharField(_('HTML Keywords'), max_length=255, **null)
    release_notes = TextField(_('Release notes'))

    class Meta:
        unique_together = ('release', 'language')


class Platform(Model):
    """A list of all platforms we release to"""
    name = CharField(_('Name'), max_length=64)
    desc = CharField(_('Description'), max_length=255)
    keywords = CharField(_('HTML Keywords'), max_length=255, **null)
    parent = ForeignKey('self', related_name='children', verbose_name=_("Parent Platform"), **null)
    manager = ForeignKey(User, verbose_name=_("Platform Manager"), **null)
    codename = CharField(max_length=255, db_index=True, **null)
    codebit = CharField(_('Code Bit Override'), max_length=64, null=True, blank=True,\
        help_text="Use this Code Name instead of the Name field "
                  "(when renaming but keeping the urls the same)")
    order = PositiveIntegerField(default=0)
    instruct = TextField(_('Instructions'), blank=True, null=True,\
        help_text=_("If supplied, this text will appear after the tabs,"
                    " but before the release notes. Will propergate to"
                    " all child platforms that do not have their own."))

    match_family = CharField(max_length=32, db_index=True,\
            help_text=_('User agent os match, whole string.'), **null)
    match_version = CharField(max_length=32, db_index=True,\
            help_text=_('User agent os version partial match, e.g. |10|11| '
                        'will match both version 10 and version 11, must ha'
                        've pipes at start and end of string.'), **null)
    match_bits = PositiveIntegerField(db_index=True, choices=((32, '32bit'), (64, '64bit')), **null)

    icon = ResizedImageField(**upload_to('icons', 32, 32))
    image = ResizedImageField(**upload_to('icons', 256, 256))

    uuid = lambda self: slugify(self.codebit or self.name)
    tab_name = lambda self: self.name
    tab_text = lambda self: self.desc
    tab_cat = lambda self: {'icon': self.icon}
    depth = lambda self: len(self.ancestors) - 1
    root = lambda self: self.ancestors()[-1]

    class Meta:
        ordering = '-order', 'codename'

    def save(self, **kwargs):
        codename = "/".join([anc.uuid() for anc in self.ancestors()][::-1])
        if self.codename != codename:
            self.codename = codename
            if self.pk:
                for child in self.children.all():
                    child.save()
        return super(Platform, self).save(**kwargs)

    def get_manager(self):
        if self.manager:
            return self.manager
        if self.parent:
            return self.parent.get_manager()
        return None

    def ancestors(self, _to=None):
        _to = _to or [self]
        if self.parent and self.parent not in _to:
            # Prevent infinite loops getting parents
            _to.append(self.parent)
            self.parent.ancestors(_to)
        return _to

    def descendants(self, _from=None):
        _from = _from or []
        for child in self.children.all():
            if child in _from:
                # Prevent infinite loops getting children
                continue
            _from.append(child)
            child.descendants(_from)
        return _from

    @property
    def instructions(self):
        """Get the nearest instructions for this platform"""
        for anc in self.ancestors():
            if anc.instruct:
                return translate_field(anc, 'instruct')

    @property
    def full_name(self):
        return " : ".join([translate_field(anc, 'name') for anc in self.ancestors()][::-1])

    def __str__(self):
        return self.full_name


class PlatformTranslation(Model):
    """A translation of a Platform"""
    platform = ForeignKey(Platform, related_name='translations')
    language = CharField(_("Language"), max_length=8, choices=OTHER_LANGS, db_index=True,
                         help_text=_("Which language is this translated into."))

    name = CharField(_('Name'), max_length=64)
    desc = CharField(_('Description'), max_length=255)
    keywords = CharField(_('HTML Keywords'), max_length=255, **null)
    instruct = TextField(_('Instructions'), blank=True, null=True)

    class Meta:
        unique_together = ('platform', 'language')


class PlatformQuerySet(QuerySet):
    def __init__(self, *args, **kw):
        super(PlatformQuerySet, self).__init__(*args, **kw)
        self.query.select_related = True

    def for_os(self, family, version, bits):
        """Returns all ReleasePlatforms that match the given user_agent os"""
        qs = self.filter(platform__match_family=family)
        # Set version to a single point precision
        version = '|' + str(version) + '|'
        qs = qs.filter(Q(platform__match_version__contains=version) |
                       Q(platform__match_version__isnull=True) |
                       Q(platform__match_version=''))
        qs = qs.filter(Q(platform__match_bits=bits) |
                       Q(platform__match_bits__isnull=True))
        return qs.order_by('platform__match_family', 'platform__match_version')

    def for_level(self, parent=''):
        """Returns a list of Platforms which are in this release"""
        # This conditional is required because codename at the zeroth
        # level is '' but the first level is 'windows', they have the
        # same number of forward slashes.
        level = parent.count('/') + 2 if parent else 1

        items = defaultdict(list)
        for release in self.defer('howto', 'info', 'release__html_desc', 'release__release_notes', 'release__background'):
            codename = release.platform.codename
            if codename.startswith(parent):
                items['/'.join(codename.rsplit('/')[:level])].append(release)

        # Get all platforms at this level
        qs = Platform.objects.filter(codename__in=items.keys())
        qs = qs.defer('instruct', 'desc')
        platforms = list(qs)

        # Add link to a release (download) if it's the only one so downloads
        # can be direct for users.
        for platform in platforms:
            if len(items[platform.codename]) == 1:
                platform.release = items[platform.codename][0]
        return platforms


class ReleasePlatform(Model):
    release = ForeignKey(Release, verbose_name=_("Release"), related_name='platforms')
    platform = ForeignKey(Platform, verbose_name=_("Release Platform"), related_name='releases')
    download = URLField(_('Download Link'), **null)
    resource = ForeignKey("resources.Resource", related_name='releases', **null)
    howto = URLField(_('Instructions Link'), **null)
    info = TextField(_('Release Platform Information'), **null)

    created = DateTimeField(_("Date created"), auto_now_add=True, db_index=True)

    objects = PlatformQuerySet.as_manager()

    class Meta:
        ordering = ('platform__parent_id',)

    def __str__(self):
        return "%s - %s" % (self.release, self.platform)

    def get_url_kwargs(self):
        kwargs = {'version': self.release.version,
                  'platform': self.platform.codename}
        if self.release.project_id:
            kwargs['project'] = self.release.project_id
        return kwargs

    def get_absolute_url(self):
        return reverse('releases:platform', kwargs=self.get_url_kwargs())

    def get_download_url(self):
        """Returns a download link with a thank you"""
        return reverse('releases:download', kwargs=self.get_url_kwargs())

    def get_resource_url(self):
        """Returns the download url or the resources download url"""
        if self.resource:
            return reverse('download_resource', kwargs={
                'pk': self.resource_id,
                'fn': self.resource.filename(),
            })
        return self.download

    @property
    def parent(self):
        if self.platform.parent_id:
            return ReleasePlatform(release=self.release, platform=self.platform.parent)
        return self.release

    def breadcrumb_name(self):
        return translate_field(self.platform, 'name')

    @property
    def instructions(self):
        if self.info:
            return translate_field(self, 'info')
        return self.platform.instructions


class ReleasePlatformTranslation(Model):
    release_platform = ForeignKey(ReleasePlatform, related_name='translations')
    language = CharField(_("Language"), max_length=8, choices=OTHER_LANGS, db_index=True,
                         help_text=_("Which language is this translated into."))

    howto = URLField(_('Instructions Link'), **null)
    info = TextField(_('Release Platform Information'), **null)

    class Meta:
        unique_together = ('release_platform', 'language')

