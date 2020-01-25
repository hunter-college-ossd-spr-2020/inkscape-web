#
# Copyright 2016-2018, Martin Owens <doctormo@gmail.com>
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
# pylint: disable=too-many-ancestors
#
"""
Forum forms, over-riding the django_comment forms.
"""

import re

from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.template.defaultfilters import striptags
from django.conf import settings

from django.forms import (
    Form, ModelForm, CharField, ValidationError, BooleanField, IntegerField,
    ModelChoiceField, ModelMultipleChoiceField, CheckboxSelectMultiple
)

from django_comments.forms import CommentForm, ContentType, ErrorDict, COMMENT_MAX_LENGTH
from django_comments.models import Comment, CommentFlag

from resources.models import Resource
from person.models import Team, User

from .widgets import TextEditorWidget
from .fields import ResourceList
from .models import ForumTopic, BannedWords
from .alert import ForumTopicAlert
from .utils import clean_comment

EMOJI = re.compile(r'([\u263a-\U0001f645])')
MENTION = re.compile(r'(^|[^>\w~])@(?P<name>[\w-]+)')
MENTION_FIX = re.compile(r'~@(?P<name>[\w-]+)')
FORUM_NOT_READY = getattr(settings, 'FORUM_NOT_READY', False)
COMMENT_EDITED = "*"

def replace_mention(match):
    """The ckeditor won't always attack links/mentions correctly."""
    prefix = match.group()[0]
    name = match.groupdict()['name']
    try:
        group = Team.objects.get(slug=name.lower())
        return '{}<a href="{}">@{}</a>'.format(
            prefix, group.get_absolute_url(), name.lower())
    except Team.DoesNotExist:
        pass
    try:
        user = User.objects.get(username=name)
        return '{}<a href="{}">@{}</a>'.format(
            prefix, user.get_absolute_url(), name)
    except User.DoesNotExist:
        return '{}@{}'.format(prefix, name)

def fix_mention(match):
    """A link created by the ckeditor, which is wrong (fix it here)."""
    name = match.groupdict()['name']
    try:
        user = User.objects.get(username=name)
        return user.get_absolute_url()
    except User.DoesNotExist:
        return '' # No link

class AttachmentMixin(object):
    """
    Basic attachments for comments and topics.
    """
    attachments = ResourceList(required=False,\
        help_text=_("A comma seperated list of resource ids to attach as files."))
    galleries = ResourceList(required=False,\
        help_text=_("A comma seperated list of resource ids to show in a gallery."))
    embedded = ResourceList(required=False,\
        help_text=_("A comma seperated list of resource ids used in the comment html."))

    def clean_comment(self):
        """Pick out all emojis and protect against multi-posting"""
        new_user = False
        if not self.user.has_perm('forums.can_post_comment'):
            if FORUM_NOT_READY:
                raise ValidationError("The Forum is not open yet. Please post your question in other parts of the website.")
            unmoderated = Comment.objects.filter(
                user=self.user,
                is_public=False,
                is_removed=False)
            if unmoderated.count() >= 2:
                raise ValidationError(
                    _("You can not post more than 2 comments awaiting moderation"))
            new_user = True

        if self.user.forum_flags.banned().count():
            raise ValidationError(
                _("You have been banned from posting to this forum!"))

        comment = self.cleaned_data['comment']
        subject = self.cleaned_data.get('subject', '')
        self.censor_text(subject.lower(), comment.lower(), new_user=new_user)

        # Add any un-matched references to users and groups
        comment = MENTION.sub(replace_mention, comment)
        comment = MENTION_FIX.sub(fix_mention, comment)

        return EMOJI.sub(r'<span class="emoji">\1</span>', comment)

    def censor_text(self, title, body, new_user=True):
        """Check if the comment has been banned"""
        censor = False
        for bwd in BannedWords.objects.all():
            if (new_user or not bwd.new_user) and (
                    (bwd.in_title and bwd.phrase in title)
                 or (bwd.in_body and bwd.phrase in body)):
                bwd.found_count += 1
                bwd.save()
                if bwd.ban_user:
                    self.user.forum_flags.instant_ban(self.user)
                    raise ValidationError("Instant ban! Please contact the moderators for help.")
                censor = True
        if censor:
            raise ValidationError(_("Post has been blocked."))


    def clean_attachments(self):
        """Make sure we can save attachments"""
        from resources.models import Category
        try:
            self.fat = Category.objects.get(slug='fat')
        except Category.DoesNotExist:
            raise ValidationError("Category for forum attachments doesn't exist, refusing to"\
                " allow forum attachments! (please ask the website admin to enable attachments)")
        return self.cleaned_data['attachments']

    def save_attachments(self, comment):
        """Save attachments to the given comment"""
        from resources.models import Resource

        # Collect the attachments
        attachments = self.cleaned_data['attachments']
        galleries = self.cleaned_data['galleries']
        embedded = self.cleaned_data['embedded']

        # collect all existing attachments that are being removed
        to_delete = comment.attachments.exclude(resource__in=attachments)\
                                       .exclude(resource__in=galleries)\
                                       .exclude(resource__in=embedded)
        # Remove any resource objects that still have a Forum Attachments category
        Resource.objects.filter(category=self.fat, pk__in=to_delete.values_list('resource_id'))
        # Delete any links to resources, this only deletes attachments that are not
        # Forum Attachment categorised because those links were removed in the cascade
        to_delete.delete()

        for inline, qset in enumerate([attachments, galleries, embedded]):
            # inline is 0 for first item and 1 for second item
            for resource in qset:
                # Update any blank categories with the forum category
                if resource.category is None:
                    Resource.objects.filter(pk=resource.pk).update(category=self.fat)
                comment.attachments.update_or_create(resource=resource,
                                                     defaults={'inline': inline})

    @staticmethod
    def initial_attachments(comment):
        """Hack the initial kwarg to set any previous attachments"""
        yield ('attachments', comment.attachments.filter(inline=0))
        yield ('galleries', comment.attachments.filter(inline=1))
        yield ('embedded', comment.attachments.filter(inline=2))


class AddCommentForm(AttachmentMixin, CommentForm):
    """This CommentForm replaces the django_comments one, what it provides is
       comment thread locking which is global no matter where the comment is.
    """
    attachments = AttachmentMixin.attachments
    galleries = AttachmentMixin.galleries
    embedded = AttachmentMixin.embedded

    # Remove fields from CommentForm, Meta exclude doesn't work
    # because this isn't a ModelForm, but a bog standard Form
    url = None
    name = None
    email = None

    def __init__(self, user, ip_address, *args, **kwargs):
        self.user = user
        self.ip_address = ip_address
        super().__init__(*args, **kwargs)
        self.fields['comment'].widget = TextEditorWidget(configuration='CKEDITOR_FORUM')

    def is_locked(self, **kw):
        """Return true if this configured comment form is locked"""
        pkey = kw.get('object_pk', self.initial['object_pk'])
        if isinstance(self.target_object, ForumTopic):
            topics = ForumTopic.objects.filter(pk=pkey)
        else:
            ctype = ContentType.objects.get_for_model(self.target_object).pk
            topics = ForumTopic.objects.filter(object_pk=pkey, forum__content_type_id=ctype)
        return any(topics.values_list('locked', flat=True))

    def clean_object_pk(self):
        """Check to see if this object is locked"""
        if self.is_locked(object_pk=self.cleaned_data["object_pk"]):
            raise ValidationError("This comment thread is locked.")
        return self.cleaned_data['object_pk']

    def security_errors(self):
        """Return just those errors associated with security"""
        errors = ErrorDict()
        for field in ["honeypot", "timestamp", "security_hash", "object_pk"]:
            if field in self.errors:
                errors[field] = self.errors[field]
        return errors

    def save(self, **_):
        """Use save to fill in various bits"""
        self.cleaned_data['name'] = self.user.username
        self.cleaned_data['email'] = self.user.email
        self.cleaned_data['url'] = ''

        comment = self.get_comment_object()
        comment.comment = clean_comment(comment)
        comment.user = self.user
        comment.ip_address = self.ip_address
        comment.is_public = self.user.has_perm('forums.can_post_comment')
        comment.save()

        self.save_attachments(comment)

        # Always subscribe when creating a new topic, made after comment.save
        ForumTopicAlert.auto_subscribe(self.user, comment.get_topic())
        return comment


class EditCommentForm(AttachmentMixin, ModelForm):
    """Edit a comment as a normal django model"""
    attachments = AttachmentMixin.attachments
    galleries = AttachmentMixin.galleries
    embedded = AttachmentMixin.embedded

    class Meta:
        model = Comment
        fields = ('comment', 'attachments', 'galleries', 'embedded')

    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs.setdefault('initial', {}).update(self.initial_attachments(kwargs['instance']))
        super().__init__(*args, **kwargs)
        self.fields['comment'].widget = TextEditorWidget(configuration='CKEDITOR_FORUM')

    def save(self, commit=True):
        """
        Bug: in django_comment trying to save an existing comment object leads to an error
        because the ip_address field gets mangled and causes database errors on save.

        This patch limits the save to just the comment field itself, which also protects
        a lot of other bits from being overwritten.
        """
        if self.errors:
            super().save(commit=commit)
        if commit:
            self.instance.comment = clean_comment(self.instance)
            self.instance.save(update_fields=('comment',))
            self.save_attachments(self.instance)
            # Flag this comment as edited (by this user)
            CommentFlag.objects.get_or_create(
                flag=COMMENT_EDITED,
                user=self.user,
                comment_id=self.instance.pk,
            )
        return self.instance


class NewTopicForm(AttachmentMixin, CommentForm):
    """
    Show a new Topic forum for creating new forum topics.
    """
    subject = CharField()

    # Remove fields from CommentForm, Meta exclude doesn't work
    # because this isn't a ModelForm, but a bog standard Form
    url = None
    name = None
    email = None

    # Use CKEditor Text Widget for the comment field
    comment = CharField(label=_('Comment'),\
        widget=TextEditorWidget(configuration='CKEDITOR_FORUM'),\
        max_length=COMMENT_MAX_LENGTH)
    field_order = ('subject', 'comment', 'honeypot')

    attachments = AttachmentMixin.attachments
    galleries = AttachmentMixin.galleries
    embedded = AttachmentMixin.embedded

    def __init__(self, user, ip_address, *args, **kwargs):
        self.user = user
        self.ip_address = ip_address
        super().__init__(*args, **kwargs)
        if user.is_moderator():
            self.fields['locked'] = BooleanField(
                required=False, initial=False, label=_('Topic Locked'),
                help_text=_("Start this topic locked. Useful for announcements "
                            "(moderators only)."))
            self.fields['sticky'] = IntegerField(
                required=False, initial=0, label=_('Sticky Priority'),
                help_text=_("Pins the thread to the top of the thread list, "
                    "the higher the number the nearer the top (moderators only)."))

    def save(self, **_):
        """Save the comment under a topic's object"""
        subject = self.cleaned_data['subject']

        att = bool(self.cleaned_data['attachments'])
        gal = bool(self.cleaned_data['galleries'])
        emb = bool(self.cleaned_data['embedded'])

        can_post = self.user.has_perm('forums.can_post_topic')
        locked = self.cleaned_data.get('locked', (not can_post))
        sticky = self.cleaned_data.get('sticky', 0)

        topic = self.target_object.topics.create(
            subject=subject, last_posted=now(),
            locked=locked, sticky=sticky,
            first_username=self.user.username,
            last_username=self.user.username,
            has_attachments=(att or gal or emb))


        # The comment's target is the topic object
        self.target_object = topic
        self.cleaned_data['name'] = self.user.username
        self.cleaned_data['email'] = self.user.email
        self.cleaned_data['url'] = ''

        comment = self.get_comment_object()
        comment.comment = clean_comment(comment)
        comment.user = self.user
        comment.ip_address = self.ip_address
        comment.is_public = can_post
        comment.save()

        # Always subscribe when creating a new topic, made after comment.save
        ForumTopicAlert.auto_subscribe(self.user, topic)

        self.save_attachments(comment)
        return self.target_object

class CommentsChoiceField(ModelMultipleChoiceField):
    """Custom display for comments list selection"""
    widget = CheckboxSelectMultiple()
    def label_from_instance(self, obj):
        return "#{}: {}".format(obj.id, striptags(obj.comment))

class SplitTopic(Form):
    """
    Controls the splitting of topics into two topic objects.
    """
    new_name = CharField(help_text=_('The new name for the split topic.'))
    comments = CommentsChoiceField(queryset=Comment.objects.none())

    def __init__(self, from_topic, **kwargs):
        super().__init__(**kwargs)
        self.from_topic = from_topic
        self.fields['comments'].queryset = from_topic.comments

    def clean_comments(self):
        """Reject a split if all the comments are selected"""
        comments = self.cleaned_data['comments']
        if len(comments) == self.from_topic.comments.count():
            raise ValidationError(_("You can not select every comment to split!"))
        return comments

    def save(self):
        """Do the splitting of the topic and make a new topic"""
        comments = self.cleaned_data['comments']
        new_name = self.cleaned_data['new_name']

        forum = self.from_topic.forum
        new_topic = forum.topics.create(subject=new_name)

        for comment in comments:
            comment.object_pk = new_topic.pk
            comment.content_type = ForumTopic.content_type()
            comment.save(update_fields=('object_pk', 'content_type'))

        self.from_topic.refresh_meta_data()
        new_topic.refresh_meta_data()
        return new_topic

class MergeTopics(Form):
    """
    Control merging of topics into one big thread.
    """
    with_topic = ModelChoiceField(queryset=ForumTopic.objects.all())

    def __init__(self, from_topic, **kwargs):
        super().__init__(**kwargs)
        self.from_topic = from_topic

    def clean_with_topic(self):
        """Make sure topics aren't the same topic"""
        with_topic = self.cleaned_data['with_topic']
        if with_topic == self.from_topic:
            raise ValidationError(_('Merged topics must be different.'))
        return with_topic

    def save(self):
        """Merge the topics, delete the from_topic once complete"""
        with_topic = self.cleaned_data['with_topic']
        with_comment = with_topic.comments.first()
        comments = self.from_topic.comments
        comments.update(
            object_pk=with_comment.object_pk,
            content_type=with_comment.content_type,
        )
        self.from_topic.delete()
        return with_topic


class CommentFlagForm(ModelForm):
    """Allow users to place flags on comments (emoji)"""
    class Meta:
        model = CommentFlag
        fields = ('flag',)

    reserved_flags = [COMMENT_EDITED]

    def clean_flag(self):
        """Make sure we never allow users to create a reserved flag"""
        flag = self.cleaned_data['flag']
        if flag in self.reserved_flags:
            raise ValidationError("Reserved Flag can not be set!")
        return flag
