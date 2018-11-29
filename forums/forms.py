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
"""
Forum forms, over-riding the django_comment forms.
"""

import re

from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

from django.forms import ModelForm, CharField, ValidationError

from django_comments.forms import CommentForm, ContentType, ErrorDict, COMMENT_MAX_LENGTH
from django_comments.models import Comment

from .widgets import TextEditorWidget
from .fields import ResourceList
from .models import ForumTopic

emoji = re.compile(r'([\u263a-\U0001f645])')

class AttachmentMixin(object):
    """
    Basic attachments for comments and topics.
    """
    attachments = ResourceList(required=False,\
        help_text=_("A comma seperated list of resource ids to attach as files."))
    inlines = ResourceList(required=False,\
        help_text=_("A comma seperated list of resource ids to show inline."))

    def clean_comment(self):
        """Pick out all emojis"""
        comment = self.cleaned_data['comment']
        return emoji.sub(r'<span class="emoji">\1</span>', comment)

    def save_attachments(self, comment):
        """Save attachments to the given comment"""
        from resources.models import Category, Resource

        fat = Category.objects.get_or_create(slug='fat', defaults={
            'name': 'Forum Attachment', 'desc': 'Attached to a forum only.',
            'selectable': False, 'filterable': False,
        })[0]

        # Collect the attachments and inlines
        attachments = self.cleaned_data['attachments']
        inlines = self.cleaned_data['inlines']

        # collect all existing attachments that are being removed
        to_delete = comment.attachments.exclude(resource__in=attachments)\
                                       .exclude(resource__in=inlines)
        # Remove any resource objects that still have a Forum Attachments category
        Resource.objects.filter(category=fat, pk__in=to_delete.values_list('resource_id'))
        # Delete any links to resources, this only deletes attachments that are not
        # Forum Attachment categorised because those links were removed in the cascade
        to_delete.delete()

        for inline, qset in enumerate([attachments, inlines]):
            # inline is 0 for first item and 1 for second item
            for resource in qset:
                comment.attachments.update_or_create(resource=resource,
                                                     defaults={'inline': inline})

    @staticmethod
    def initial_attachments(comment):
        """Hack the initial kwarg to set any previous attachments"""
        yield ('attachments', comment.attachments.filter(inline=False))
        yield ('inlines', comment.attachments.filter(inline=True))


class AddCommentForm(AttachmentMixin, CommentForm):
    """This CommentForm replaces the django_comments one, what it provides is
       comment thread locking which is global no matter where the comment is.
    """
    attachments = AttachmentMixin.attachments
    inlines = AttachmentMixin.inlines

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
        comment.user = self.user
        comment.ip_address = self.ip_address
        comment.is_public = self.user.has_perm('forums.can_post_comment')
        comment.save()

        self.save_attachments(comment)
        return comment


class EditCommentForm(AttachmentMixin, ModelForm):
    """Edit a comment as a normal django model"""
    attachments = AttachmentMixin.attachments
    inlines = AttachmentMixin.inlines

    class Meta:
        model = Comment
        fields = ('comment', 'attachments', 'inlines')

    def __init__(self, *args, **kwargs):
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
            self.instance.save(update_fields=('comment',))
            self.save_attachments(self.instance)
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
    inlines = AttachmentMixin.inlines

    def __init__(self, user, ip_address, *args, **kwargs):
        self.user = user
        self.ip_address = ip_address
        super().__init__(*args, **kwargs)

    def save(self, **_):
        """Save the comment under a topic's object"""
        subject = self.cleaned_data['subject']

        att = bool(self.cleaned_data['attachments'])
        inl = bool(self.cleaned_data['inlines'])

        self.target_object = self.target_object.topics.create(
            subject=subject, last_posted=now(),
            last_username=self.user.username,
            has_attachments=(att or inl))

        self.cleaned_data['name'] = self.user.username
        self.cleaned_data['email'] = self.user.email
        self.cleaned_data['url'] = ''

        comment = self.get_comment_object()
        comment.user = self.user
        comment.ip_address = self.ip_address
        comment.is_public = self.user.has_perm('forums.can_post_topic')
        comment.save()

        self.save_attachments(comment)
        return self.target_object
