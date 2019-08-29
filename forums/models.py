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
"""
Forums are a simple extension of django_comments and there really
shouldn't be much functionality contained within this app.
"""

import json
from datetime import datetime, timedelta

from unidecode import unidecode

from django.apps import apps
from django.db.models.functions import Cast
from django.db.models import (
    Model, Manager, CASCADE, SET_NULL,
    ForeignKey, OneToOneField, IntegerField, DateTimeField, BooleanField,
    CharField, SlugField, TextField, PositiveIntegerField,
)
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.validators import MaxLengthValidator
from django.conf import settings

from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import make_aware
from django.utils.encoding import force_text
from django.utils.text import slugify
from django_comments.models import Comment
from resources.models import Resource
from person.models import Team

from .querysets import ForumQuerySet, TopicQuerySet, UserFlagQuerySet
from .fields import IconField

APP = apps.get_app_config('forums')

class ForumGroup(Model):
    name = CharField(max_length=128, unique=True)

    parent = property(lambda self: self.forums.all().parent)

    def __str__(self):
        return self.name

class Forum(Model):
    """A collection of topics for discussion"""
    group = ForeignKey(ForumGroup, related_name='forums')
    sort = IntegerField(default=0, null=True, blank=True)

    name = CharField(max_length=128, unique=True)
    slug = SlugField(max_length=128, unique=True)
    desc = TextField(validators=[MaxLengthValidator(1024)], null=True, blank=True)
    icon = IconField(upload_to='forum/icon', null=True, blank=True,\
        fallback='forums/images/fallback_icon.svg')

    lang = CharField(max_length=8, null=True, blank=True,\
        help_text=_('Set this ONLY if you want this forum restricted to this language'))
    team = ForeignKey(Team, null=True, blank=True,\
        help_text=_('Set this ONLY if you want this forum restricted to this team.'))

    content_type = ForeignKey(ContentType, verbose_name=_('Fixed Content From'),\
        help_text=_("When fixed content is set, new topics can not be created. Instead, "
                    "commented items are automatically posted as topics."), null=True, blank=True)
    sync = CharField(max_length=64, choices=APP.sync_choices, verbose_name=_('Sync From'),\
         help_text=_("When sync source is set, new topics and messages can not be created. "
                     "Instead, sync messages are collated into topics and replies by scripts."),
                     null=True, blank=True)

    post_count = PositiveIntegerField(_('Number of Posts'), default=0)
    last_posted = DateTimeField(_('Last Posted'), db_index=True, null=True, blank=True)

    objects = ForumQuerySet.as_manager()

    class Meta:
        get_latest_by = 'last_posted'
        ordering = ('-sort',)

    def __str__(self):
        return self.name

    def model_class(self):
        """Return a content type class if this forum is based on objects"""
        if self.content_type:
            return self.content_type.model_class()
        return ForumTopic

    def get_absolute_url(self):
        """Return a link to this forum"""
        return reverse('forums:topic_list', kwargs={'slug': self.slug})

    def save(self, **kwargs):
        """Save and add a slug if not yet created"""
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        return super(Forum, self).save(**kwargs)

    @property
    def comments(self):
        """Returns a queryset of all comments on all the topics in this forum"""
        if self.content_type:
            # Count all comments that have this content type
            return Comment.objects.filter(content_type=self.content_type)

        # Count only topics which are in this forum, content_type links use
        # a generic CharField for primaryKeys, so to match them we have to
        # convert the keys to a string in the database.
        objects = self.topics.annotate(str_id=Cast('pk', CharField(max_length=32)))
        return Comment.objects.filter(
            content_type=ForumTopic.content_type(),
            object_pk__in=objects.values_list('str_id'),
        )

    @property
    def public_comments(self):
        """Like comments, but restricted to non-removed comments"""
        return self.comments.filter(is_removed=False)

    def refresh_meta_data(self, last=None):
        """Refresh all the meta-data fields"""
        if last is None:
            last = self.comments.last()
            self.post_count = self.public_comments.count()
        else:
            self.post_count += 1
        if last:
            self.last_posted = last.submit_date
        self.save(update_fields=['post_count', 'last_posted'])

    @property
    def sync_config(self):
        """Return a configuration for forum sync plugins"""
        return settings.FORUM_SYNCS.get(self.sync, {})

    def sync_message(self, message):
        """Add a new message xor forum topic based on an import"""
        if not message:
            return
        objects = CommentLink.objects
        message_id = message.get_message_id()
        reply_id = message.get_reply_id()

        links = objects.filter(message_id=message_id)
        if links.count() == 1:
            return links.get().comment

        reply_to = objects.filter(message_id=reply_id)
        if reply_to.count() > 0:
            topic = reply_to.get().comment.content_object
            created = None
        else:
            topic, created = self.topics.get_or_create(
                message_id=message_id,
                defaults={
                    'subject': str(message.get_subject()),
                }
            )

        if created in (None, True):
            comment = Comment.objects.create(
                site_id=1,
                user=message.get_user(),
                user_name=str(message.get_username()),
                user_email=message.get_email(),
                user_url=message.get_userurl(),
                comment=force_text(message.get_body(), errors='replace'),
                submit_date=message.get_created(),
                content_object=topic,
            )

            objects.create(
                comment=comment,
                message_id=message_id,
                reply_id=reply_id,
                subject=message.get_subject(),
                extra_data=json.dumps(message.get_data()),
            )

        if created and hasattr(message, 'get_replies'):
            for reply in message.get_replies():
                comment = Comment.objects.create(
                    site_id=1,
                    user=message.get_user(),
                    user_name=str(message.get_username()),
                    user_email=message.get_email(),
                    user_url='',
                    comment=force_text(reply.get_body(), errors='replace'),
                    submit_date=message.get_created(),
                    content_object=topic,
                )

        return comment


class ForumTopic(Model):
    """When a forum allows free standing topics (without connection to an object)"""
    forum = ForeignKey(Forum, related_name='topics')
    object_pk = PositiveIntegerField(null=True, blank=True)
    subject = CharField(max_length=128)
    slug = SlugField(max_length=128, unique=True)

    message_id = CharField(max_length=255, db_index=True, null=True, blank=True)

    post_count = PositiveIntegerField(_('Number of Posts'), default=0)
    first_posted = DateTimeField(_('First Posted'), db_index=True,
                                 auto_now_add=True, null=True, blank=True)
    last_posted = DateTimeField(_('Last Posted'), db_index=True, null=True, blank=True)
    first_username = CharField(max_length=128, null=True, blank=True)
    last_username = CharField(max_length=128, null=True, blank=True)
    has_attachments = BooleanField(default=False)

    sticky = IntegerField(_('Sticky Priority'), default=0, null=True,\
        help_text=_('If set, will stick this post to the top of the topics '
                    'list. Higher numbers appear nearer the top. Same numbers '
                    'will appear together, sorted by date.'))
    locked = BooleanField(default=False, help_text=_('Topic is locked by moderator.'))
    removed = BooleanField(default=False, help_text=_('Topic deleted by moderator.'))

    objects = TopicQuerySet.as_manager()

    class Meta:
        get_latest_by = 'last_posted'
        ordering = ('-sticky', '-last_posted',)
        permissions = (
            ("can_post_comment", "User can post comments to the forums."),
            ("can_post_topic", "User can make new forum topics."),
        )

    def __str__(self):
        return self.subject

    @classmethod
    def content_type(cls):
        """Return the content type for ForumTopic types"""
        if not hasattr(cls, '_ct'):
            cls._ct = ContentType.objects.get_for_model(cls)
        return cls._ct

    @property
    def object(self):
        """Return the focus object for this topic starter"""
        return self.forum.content_type.get_object_for_this_type(pk=self.object_pk)

    @property
    def comment_subject(self):
        """The ulimate object that all the comments point towards"""
        if self.object_pk and self.forum.content_type:
            return self.object
        return self

    @property
    def comments(self):
        """Returns a list of comment associated with this topic"""
        obj = self.comment_subject
        ctype = ContentType.objects.get_for_model(obj)
        return Comment.objects.filter(object_pk=obj.pk, content_type=ctype)

    @property
    def public_comments(self):
        """Like comments, but restricted to non-removed comments"""
        return self.comments.filter(is_removed=False)

    @property
    def object_template(self):
        """Returns a custom template if needed for this item."""
        custom_template = None
        if self.object_pk:
            ctype = self.forum.content_type
            custom_template = '%s/%s_comments.html' % (ctype.app_label, ctype.model)

        elif self.forum.sync:
            conf = self.forum.sync_config
            key = conf.get('ENGINE', self.forum.sync).split('.')[-1]
            default = 'plugins/%s_comments.html' % key
            custom_template = conf.get('TEMPLATE', default)

        if custom_template is not None:
            try:
                get_template(custom_template)
                return custom_template
            except TemplateDoesNotExist:
                pass
        return 'forums/forumtopic_header.html'

    @property
    def is_sticky(self):
        """Return true if this topic is sticky (shows at the top of forums)"""
        return bool(self.sticky)

    @property
    def is_moderated(self):
        """Return true if this topic is being moderated"""
        if self.post_count == 1:
            first = self.comments.first()
            return first and not first.is_public
        return False

    def get_absolute_url(self):
        """Return a link to this topic"""
        if self.slug:
            return reverse('forums:topic', kwargs={'forum':self.forum.slug, 'slug':self.slug})
        return "error"

    def refresh_meta_data(self, last=None, first=None):
        """Refresh all the meta-data fields"""
        if first is None:
            first = self.comments.first()
        if last is None:
            last = self.comments.last()
            self.post_count = self.public_comments.count()
        else:
            self.post_count += 1

        if first:
            self.first_posted = first.submit_date
            self.first_username = first.user.username

        if last:
            self.last_posted = last.submit_date
            self.last_username = last.user.username

        if not self.post_count:
            self.removed = True

        self.has_attachments = self.comments.filter(attachments__isnull=False).count()
        self.save(update_fields=['post_count', 'first_posted', 'last_posted',
                                 'first_username', 'last_username', 'removed'])

    def save(self, **kw):
        """Save this topic and generate a slug if needed"""
        self.subject = self.subject[:120]

        if not self.slug:
            original = slugify(unidecode(self.subject))
            self.slug = original
            while ForumTopic.objects.filter(slug=self.slug).count():
                self.slug = original + '_' + get_random_string(length=5)

        return super(ForumTopic, self).save(**kw)

class AttachmentManager(Manager):
    """Add some management functions for templates to show presentations"""
    def is_presentation(self):
        """Return true if there is one single inline attachment"""
        return len(self.inlines()) == 1

    def inlines(self):
        """Return the queryset just inlines"""
        ret = []
        for item in self.get_queryset():
            ret.append(item.inline)
        return ret

class CommentAttachment(Model):
    """A single attachment on a comment"""
    resource = ForeignKey(Resource, related_name='comment_hosts', on_delete=CASCADE)
    comment = ForeignKey(Comment, related_name='attachments', on_delete=CASCADE)
    inline = BooleanField(default=False)

    desc = CharField(max_length=128, null=True, blank=True)
    objects = AttachmentManager()

    def __str__(self):
        return "{} attached to comment in the forum.".format(self.resource)

class ModerationManager(Manager):
    """A logging manager"""
    def get_last(self, days=7):
        """Return the last number of days of logs"""
        scale = make_aware(datetime.now() - timedelta(days=days), None)
        return self.filter(performed__gte=scale)


class ModerationLog(Model):
    """
    Record each moderation action, what was done and any other details.
    """
    action = CharField(max_length=128)
    moderator = ForeignKey(settings.AUTH_USER_MODEL, related_name="forum_moderation_actions")
    performed = DateTimeField(auto_now=True, db_index=True)

    user = ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=SET_NULL)
    comment = ForeignKey(Comment, null=True, blank=True,
                         on_delete=SET_NULL, related_name='mlog')
    topic = ForeignKey(ForumTopic, null=True, blank=True,
                       on_delete=SET_NULL, related_name='mlog')
    forum = ForeignKey(Forum, null=True, blank=True,
                       on_delete=SET_NULL, related_name='mlog')

    detail = TextField(null=True, blank=True)
    objects = ModerationManager()

    class Meta:
        ordering = ('performed',)

    def __str__(self):
        return self.action

    def details(self):
        try:
            return json.loads(self.detail)
        except ValueError:
            return {}


class UserFlag(Model):
    """
    Record a flag on a user. Much like the comment flag functionality in
    django_comments app, this is a flexible way to tag users with all sorts of
    important social symbols and flags.
    """
    FLAG_BANNED = "\U0001f6ab" # User is banned from posting comments
    FLAG_MODERATOR = '\u2696' # User is a moderator on the website

    user = ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'),
                      related_name="forum_flags", on_delete=CASCADE)
    # Translators: 'flag' is a noun here.
    flag = CharField(_('flag'), max_length=5, db_index=True)
    title = CharField(_('title'), max_length=128, null=True, blank=True)
    modflag = BooleanField(default=False,
        help_text="If true, this flag is only visible to moderators.")
    created = DateTimeField(auto_now_add=True, null=True, blank=True)

    objects = UserFlagQuerySet.as_manager()

    class Meta:
        unique_together = [('user', 'flag')]
        verbose_name = _('user forum flag')
        verbose_name_plural = _('user forum flags')

    def __str__(self):
        return "%s flag of forum user %s (%s)" % (
            self.flag, self.user.get_username(), self.title
        )

class CommentLink(Model):
    """We extend our comment model with links to sync'd or imported comments"""
    comment = OneToOneField(Comment, related_name='link')

    message_id = CharField(max_length=255, db_index=True, unique=True,
                           help_text="A unique identifier for this message")
    reply_id = CharField(max_length=255, null=True, blank=True, db_index=True,
                         help_text="Either the previous message in the chain, or the parent id")
    subject = CharField(max_length=255, null=True, blank=True, db_index=True,
                        help_text="A matchable subject line for this comment.")

    extra_data = TextField(null=True, blank=True)

    def __str__(self):
        return self.message_id
