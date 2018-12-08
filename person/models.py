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
"""Customise the user model"""

import os

from datetime import timedelta

from django.conf import settings
from django.db.models.signals import post_save
from django.db.models import (
    F, Q, QuerySet, Max, Model, Manager, TextField, CharField, URLField,
    DateTimeField, BooleanField, IntegerField, ForeignKey, SlugField,
    ImageField,
)
from django.utils.timezone import now
from django.dispatch import receiver

from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _, get_language
from django.core.urlresolvers import reverse
from django.core.validators import MaxLengthValidator
from django.contrib.sessions.models import Session
from django.contrib.auth import SESSION_KEY

from django.contrib.auth.models import Group, AbstractUser, UserManager, Permission
from inkscape.fields import ResizedImageField, AutoOneToOneField

null = dict(null=True, blank=True) # pylint: disable=invalid-name

def linked_users_only(qset, *rels):
    """
    Limits a query to only include enough user information to link to the user.
    """
    only = []
    for rel in rels:
        #for field in ('first_name', 'last_name', 'username'):
        for field in ('photo', 'bio', 'gpg_key', 'last_seen', 'website'):
            only.append(rel + '__' + field)
    return qset.select_related(*rels).defer(*only)

class PersonManager(UserManager):
    """Overwrite the creation functions because we customise is_staff"""
    def get_queryset(self):
        """Defer the gpg_key field, as it's not required the vast mojority of the time"""
        return super(PersonManager, self).get_queryset().defer('gpg_key')

    def _create_user(self, username, email, password, **extra_fields):
        add_is_staff = extra_fields.pop('is_staff', False)
        user = super()._create_user(username, email, password, **extra_fields)
        if add_is_staff:
            user.user_permissions.add(Permission.objects.get(codename='is_staff'))
        return user

class User(AbstractUser):
    """
    Take over the django auth user and provide a list of new fields as a user account.
    """
    bio = TextField(_('Bio'), validators=[MaxLengthValidator(4096)], **null)
    photo = ResizedImageField(_('Photograph (square)'), upload_to='photos',
                              max_width=190, max_height=190, **null)
    language = CharField(_('Default Language'), max_length=8, choices=settings.LANGUAGES, **null)

    ircnick = CharField(_('IRC Nickname'), max_length=20, **null)
    ircpass = CharField(_('Freenode Password (optional)'), max_length=128, **null)

    dauser = CharField(_('deviantArt User'), max_length=64, **null)
    ocuser = CharField(_('Openclipart User'), max_length=64, **null)
    tbruser = CharField(_('Tumblr User'), max_length=64, **null)
    website = URLField(_('Website or Blog'), **null)
    gpg_key = TextField(_('GPG Public Key'), validators=[MaxLengthValidator(262144)],\
        help_text=_('<strong>Signing and Checksums for Uploads</strong><br/> '
                    'Either fill in a valid GPG key, so you can sign your uploads, '
                    'or just enter any text to activate the upload validation feature '
                    'which verifies your uploads by comparing checksums.<br/>'
                    '<strong>Usage in file upload/editing form:</strong><br/>'
                    'If you have submitted a GPG key, you can upload a *.sig file, '
                    'and your upload can be verified. You can also submit these '
                    'checksum file types:<br/>'
                    '*.md5, *.sha1, *.sha224, *.sha256, *.sha384 or *.sha512'), **null)

    last_seen = DateTimeField(**null)
    visits = IntegerField(default=0)

    # Replaces is_staff from the parent abstractuser
    is_admin = BooleanField(_('staff status'), default=False, db_column='is_staff',\
        help_text=_('Designates whether the user can log into this admin site.'))

    objects = PersonManager()

    class Meta:
        permissions = [
            ("use_irc", _("IRC Chat Training Complete")),
            ("website_cla_agreed", _("Agree to Website License")),
            ("is_staff", "Staff permissions are automatically granted."),
        ]
        db_table = 'auth_user'

    def __str__(self):
        return self.name

    @property
    def is_staff(self):
        """
        Returns true if the user is a staff member (can access admin)
        takes over from the django is_staff field which we replace with
        a permission to allow groups of people to be staff.
        """
        return self.is_admin or self.has_perm('person.is_staff')

    def is_moderator(self):
        """Returns true if the user is a moderator"""
        return self.has_perm("moderation.can_moderate")

    @property
    def name(self):
        """Return either the full name of the user or the username"""
        if self.first_name or self.last_name:
            return self.get_full_name()
        return self.username

    def get_ircnick(self):
        """Return the irc nickname or the username (default)"""
        if not self.ircnick:
            return self.username
        return self.ircnick

    def photo_url(self):
        """Return the photo url if it exist"""
        if self.photo:
            return self.photo.url
        return None

    def photo_preview(self):
        """Returns a photo preview or a default svg file"""
        if self.photo:
            return '<img src="%s" style="max-width: 200px; max-height: 250px;"/>' % self.photo.url
        # Return an embedded svg, it's easier than dealing with static files.
        return """
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="200" height="250">
           <path style="stroke:#6c6c6c;stroke-width:.5px;fill:#ece8e6;"
           d="m1.2 1.2v248h27.6c-9.1-43 8-102 40.9-123-49.5-101 111-99.9 61.5 1.18 36.6 35.4 48.6 78.1 39.1 122h28.5v-248z"
           /></svg>"""
    photo_preview.allow_tags = True

    def quota(self):
        """Returns the amount of quota (disk space) this use has in total (not remaining)"""
        from resources.models import Quota
        groups = Q(group__in=self.groups.all()) | Q(group__isnull=True)
        quotas = Quota.objects.filter(groups)
        if quotas.count():
            return quotas.aggregate(Max('size'))['size__max'] * 1024
        return 0

    def get_absolute_url(self):
        """Return the url to the user's profile page"""
        if not self.username:
            return '/'
        return reverse('view_profile', kwargs={'username':self.username})

    def visited_by(self, by_user):
        """Adds one to the user's visitor count"""
        if by_user != self:
            self.visits += 1
            self.save(update_fields=['visits'])

    @property
    def teams(self):
        """Returns a queryset of teams this user is a member of"""
        return Team.objects.filter(group__in=self.groups.all())

    def viewer_is_subscribed(self, user):
        """Returns true if the calling user is subscribed to this user's resources."""
        if user.is_authenticated():
            return bool(self.resources.subscriptions().get(user=user.pk))
        return False


@receiver(post_save, sender=User)
def is_active_check(sender, instance, **_):
    """Delete every session when active is False"""
    if not instance.is_active:
        for session in Session.objects.all():
            # There is google-oauth sessions which aren't cleared here
            try:
                if int(session.get_decoded().get(SESSION_KEY, -1)) == instance.pk:
                    session.delete()
            except sender.DoesNotExist:
                pass

def group_breadcrumb_name(self):
    """Return the name of the group for breadcrumbs"""
    try:
        return str(self.team)
    except UnicodeDecodeError:
        return str(self)
Group.breadcrumb_name = group_breadcrumb_name


class TwilightSparkle(Manager):
    """The queryset manager for frienships"""
    def i_added(self, user):
        """Return true if I have added this friend before"""
        try:
            return user.is_authenticated() and bool(self.get(from_user=user.pk))
        except Friendship.DoesNotExist:
            return False

    def mutual(self):
        """Returns a mutual set of friends"""
        return self.get_queryset()\
                .filter(from_user__from_friends__from_user=F('user'))

class Friendship(Model):
    """A single instance of friendship"""
    from_user = ForeignKey(User, related_name='friends')
    user = ForeignKey(User, related_name='from_friends')

    objects = TwilightSparkle()

    def __str__(self):
        return u"%s is friends with %s" % (str(self.from_user), str(self.user))

class TeamChatRoom(Model):
    """An ChatRoom for a team"""
    team = ForeignKey('Team', related_name='ircrooms')
    admin = ForeignKey(User, **null)
    channel = CharField(_('Chatroom Name'), max_length=64)
    language = CharField(max_length=5, default='en', choices=settings.LANGUAGES)

    class Meta:
        unique_together = (('language', 'team'),)

    def __str__(self):
        return 'IRC: %s' % self.channel

    @property
    def log_path(self):
        """Return the path to the IRC logs"""
        if hasattr(settings, 'IRC_LOGS'):
            return os.path.join(settings.IRC_LOGS, self.channel)
        return None

    def logs(self):
        """Returns a list of logs for this chatroom"""
        path = self.log_path
        if path is not None:
            url = path.replace(settings.MEDIA_ROOT, settings.MEDIA_URL)
            if os.path.isdir(path):
                for filename in sorted(os.listdir(path)):
                    yield {
                        'url': os.path.join(url, filename),
                        'name': filename.replace('.txt', ''),
                    }


class TeamMembership(Model):
    """
    A team membership exists when a user joins a team, existance doesn't mean
    they are a member of that team, just that they were, are or will be one.

    It functions as a record of when a user joined a team, when they should
    expire from the team and what date time they did expire.

    Joining a team sets the 'joined' datetime, which tags this user as
    a current member. It will also unset the 'expired' field.

    Leaving a team (manually or automatically) sets the 'expired' datetime
    which tags this user as being a 'past' member.
    """
    team = ForeignKey('Team', related_name='memberships')
    user = ForeignKey(User, related_name='memberships')

    requested = DateTimeField(**null)
    joined = DateTimeField(**null)
    expired = DateTimeField(**null)

    added_by = ForeignKey(User, related_name='has_added_users', **null)
    removed_by = ForeignKey(User, related_name='has_removed_users', **null)

    title = CharField(_('Role Title'), max_length=128, **null)
    style = CharField(_('Role Style'), max_length=64, **null)

    @property
    def is_watcher(self):
        """Return true if this user is watching this team"""
        return not self.requested and not self.joined and not self.is_expired

    @property
    def is_requester(self):
        """Return true if this user is requesting membership to team"""
        return bool(self.requested) and not self.joined and not self.is_expired

    @property
    def is_member(self):
        """Return true if this user is a member of this team"""
        return self.joined and not self.is_expired

    @property
    def is_expired(self):
        """Return true if this user is expired"""
        return not (self.expired is None or self.expired > timezone.now())

    class Meta:
        unique_together = ('team', 'user')

    def save(self, **kwargs): # pylint: disable=arguments-differ
        """Control the group of users (which grants permissions)"""
        super(TeamMembership, self).save(**kwargs)
        if self.id:
            self.update_group()

    def update_group(self):
        """
        Makes sure the user is registered in the right group. Keeping
        the team membership and the group permissions sync'ed.
        """
        user_group = self.team.group.user_set
        if not self.is_expired and self.joined:
            user_group.add(self.user)
        else:
            user_group.remove(self.user)


class Team(Model):
    """
    A team is a shadow object for a group, it doesn't record a list of users that
    is done by django.auth.Group, but it does control everything else about memberships.
    """
    ENROLES = (
        ('O', _('Open')),
        ('P', _('Peer Approval')),
        ('T', _('Admin Approval')),
        ('C', _('Closed')),
        ('S', _('Secret')),
        ('E', _('Elected')),
    )
    ICON = os.path.join(settings.STATIC_URL, 'images', 'team.svg')

    admin = ForeignKey(User, related_name='admin_teams', **null)
    group = AutoOneToOneField(Group, related_name='team')
    email = CharField(max_length=256, **null)

    name = CharField(_('Team Name'), max_length=32)
    slug = SlugField(_('Team URL Slug'), max_length=32)
    icon = ImageField(_('Display Icon'), upload_to='teams', default=ICON)

    order = IntegerField(default=0)
    intro = TextField(_('Introduction'), validators=[MaxLengthValidator(1024)],\
        help_text=_("Text inside the team introduction."), **null)
    desc = TextField(_('Full Description'), validators=[MaxLengthValidator(10240)],\
        help_text=_("HTML description on the teams front page."), **null)
    charter = TextField(_('Charter'), validators=[MaxLengthValidator(30240)],\
        help_text=_("HTML page with rules for team members."), **null)
    side_bar = TextField(_('Side Bar'), validators=[MaxLengthValidator(10240)],\
        help_text=_("Extra sie bar for buttons and useful links."), **null)

    mailman = CharField(_('Email List'), max_length=32, null=True, blank=True,\
        help_text='The name of the pre-configured mailing list for this team')
    enrole = CharField(_('Enrollment'), max_length=1, default='O', choices=ENROLES)

    auto_expire = IntegerField(default=0,\
        help_text=_('Number of days that members are allowed to be a member.'))

    localized_fields = ('name', 'intro', 'desc', 'charter', 'side_bar')

    class Meta:
        ordering = ('order',)

    @property
    def channels(self):
        """Return a list of all irc channels"""
        return self.ircrooms.filter(language__in=[get_language(), 'en'])\
                .values('language', 'channel')

    @property
    def parent(self):
        """Returns the parent object, in this case a full list of teams"""
        return type(self).objects.all()

    @property
    def team(self):
        """Return self as the team, used in mixology"""
        return self

    @property
    def peers(self):
        """Return a list (not queryset) or members who can approve others"""
        if self.enrole == 'P':
            return [member.user for member in self.members] + [self.admin]
        return [self.admin]

    def get_absolute_url(self):
        """Return link to team page"""
        return reverse('team', kwargs={'team': self.slug})

    def save(self, **kwargs): # pylint: disable=arguments-differ
        if not self.name:
            self.name = self.group.name
        if not self.slug:
            self.slug = slugify(self.name)
        return super(Team, self).save(**kwargs)

    def get_members(self, joined=True, expired=False, requested=None):
        """
        Returns a QuerySet containing the given memberships as they related to
        this team. See convience functions below.

        Default is to return all joined (real) members of a team.
        """
        qset = Q()
        if expired is True:
            qset &= Q(expired__lt=timezone.now())
        elif expired is False:
            qset &= (Q(expired__isnull=True) | Q(expired__gt=timezone.now()))
        if requested is not None:
            qset &= Q(requested__isnull=not requested)
        if joined is not None:
            qset &= Q(joined__isnull=not joined)
        return self.memberships.filter(qset)

    requests = property(lambda self: self.get_members(False, False, True).order_by('-requested'))
    watchers = property(lambda self: self.get_members(False, False, False))
    members = property(lambda self: self.get_members(True).order_by('joined'))

    old_requests = property(lambda self: self.get_members(False, True, True).order_by('-expired'))
    old_watchers = property(lambda self: self.get_members(False, True, False))
    old_members = property(lambda self: self.get_members(True, True).order_by('-expired'))

    def has_member(self, user):
        """Returns true if the user is a member of the team"""
        return self.members.filter(user_id=user.id).count() == 1

    def has_requester(self, user):
        """Returns true if the user is requesting to join the team"""
        return self.requests.filter(user_id=user.id).count() == 1

    def has_watcher(self, user):
        """Returns true if the user is watching this team"""
        return self.watchers.filter(user_id=user.id).count() == 1

    def update_membership(self, user, **kw):
        """Generic update function for views to change membership"""
        obj, created = self.memberships.update_or_create(user=user, defaults=kw)
        return obj, created

    def expire_if_needed(self, before_date=None):
        """Expire any members who have expired from this team"""
        if before_date is None:
            before_date = now()
        delta = timedelta(days=self.auto_expire)
        for membership in self.members:
            if membership.joined + delta < before_date:
                self.update_membership(membership.user, expired=now(), removed_by=None)
                yield membership.user

    def warn_if_needed(self, before_date=None, days=5):
        """Warn a user they are about to be expired from the team"""
        if before_date is None:
            before_date = now()
        delta = timedelta(days=self.auto_expire - days)
        for membership in self.members:
            if (membership.joined + delta).date == before_date.date:
                # XXX Send warning email
                yield membership.user

    def __str__(self):
        return self.name


def get_team_url(self):
    """Patch in the url so we get a better front end view from the admin."""
    try:
        return self.team.get_absolute_url()
    except Team.DoesNotExist:
        return '/'
Group.get_absolute_url = get_team_url
