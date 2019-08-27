#
# Copyright 2017, Martin Owens <doctormo@gmail.com>
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
Moderation is achieved using a generic flagging model and some further
 User monitoring which should allow users to manage each other in a
 healthy community atmosphere.
"""

from django.db.models import *
from django.apps import apps

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles import storage
from django.core.validators import MaxLengthValidator
from django.dispatch import Signal

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

flag_created = Signal(providing_args=["instance", "flag", "mod"])
NULL = dict(blank=True, null=True)

class ObjectQuery(QuerySet):
    """Manage how flagged objects are dealt with."""
    @staticmethod
    def get_template(ct):
        """Get the moderation item template if available"""
        from django.template import loader

        path = "%s/%s_moderation.html" % (ct.app_label, ct.model)
        try:
            if loader.get_template(path):
                return path
        except:
            pass

    @property
    def models(self):
        """Returns a list of models with useful meta data"""
        pks = FlagObject.objects.values_list('content_type', flat=True).distinct()
        for ct in ContentType.objects.filter(pk__in=pks):
            model = ct.model_class()
            yield {
              'app': ct.app_label,
              'model': ct.model,
              'label': model.__name__,
              'objects': self.filter(content_type=ct),
              'template': self.get_template(ct),
            }
            

class FlagObject(Model):
    """
    The implicated object is a record of this object
    """
    USER_FLAG = 1
    MODERATOR_APPROVAL = -8
    MODERATOR_UNDECIDED = 0
    MODERATOR_CENSURE = 7
    FLAGS = {
      USER_FLAG: 'user_flag',
      MODERATOR_APPROVAL: 'moderator_approval',
      MODERATOR_UNDECIDED: 'moderator_undecided',
      MODERATOR_CENSURE: 'moderator_censure',
    }

    RETAIN_THRESHOLD = -10
    HIDING_THRESHOLD = 5
    DELETE_THRESHOLD = 10

    object_owner = ForeignKey(settings.AUTH_USER_MODEL,
            verbose_name=_('Owning User'), related_name="flagged",
            on_delete=SET_NULL, **NULL)

    content_type = ForeignKey(ContentType, on_delete=CASCADE)
    object_id = PositiveIntegerField(**NULL)
    updated = DateTimeField(auto_now=True)
    resolution = NullBooleanField(default=None, choices=(
        (None, _('Pending Moderator Action')),
        (True, _('Object is Retained')),
        (False, _('Object is Deleted')),
    ))

    obj = GenericForeignKey('content_type', 'object_id')
    objects = ObjectQuery.as_manager()

    def __str__(self):
        return "Flagged object: %d (%s)" % (self.pk, str(self.resolution))

    @property
    def weight(self):
        return self.votes.all().aggregate(w=Sum('weight'))['w'] or 0

    is_retained = property(lambda self: self.weight < self.RETAIN_THRESHOLD)
    is_deleted = property(lambda self: self.weight > self.DELETE_THRESHOLD)

    @property
    def was_deleted(self):
        return self.obj.resolution is False

    @property
    def is_hidden(self):
        """Return true if it's possible to hide this object"""
        return self.weight > self.HIDING_THRESHOLD and hasattr(self.obj, 'is_removed')

    @property
    def was_hidden(self):
        """Returns true if the object was hidden at some point"""
        return hasattr(self.obj, 'is_removed') and self.obj.is_removed

    @property
    def censure_votes(self):
        return len([1 for flag in self.flags if flag.weight == self.MODERATOR_CENSURE])

    @property
    def approve_votes(self):
        return len([1 for flag in self.flags if flag.weight == self.MODERATOR_APPROVAL])

    @property
    def flag_votes(self):
        return len([1 for flag in self.flags if flag.weight == self.USER_FLAG])

    @property
    def flags(self):
        if not hasattr(self, '_flags'):
            self._flags = self.votes.all()
        return self._flags

    def status_label(self):
        if self.is_retained:
            return _("retained")
        if self.was_hidden:
            return _("hidden")
        if self.is_deleted:
            return _("deleted")
        return _("undecided")


class FlagManager(Manager):
    """
    Manage when users flag items and what to do about it.
    """
    def flag(self, user, obj, weight=1, notes=""):
        """Create a new flag for this object"""
        kw = dict(
          object_id=obj.pk,
          content_type=ContentType.objects.get_for_model(obj),
          defaults={'object_owner': self.get_owner(obj)},
        )
        obj_flag, new_flag = FlagObject.objects.get_or_create(**kw)

        kw = dict(
          moderator=user,
          target=obj_flag,
          defaults={'weight': weight, 'notes': notes},
        )
        flag, created = self.get_or_create(**kw)

        if new_flag:
            flag_created.send(FlagObject, instance=obj_flag, flag=flag, mod=user)

        if not created and flag.weight != weight or not flag.notes and notes:
            if weight is not None:
                flag.weight = weight
            flag.notes = notes
            flag.save()
        return flag, created

    @staticmethod
    def get_owner(obj):
        """Get the field we think the user is in"""
        klass = type(obj)
        if hasattr(klass, 'owner_field'):
            return getattr(obj, getattr(klass, 'owner_field'))

        auth_klass = apps.get_model(*settings.AUTH_USER_MODEL.split('.',1))
        if klass is auth_klass:
            return obj
        ret = []
        for field in klass._meta.fields:
            try:
                if field.rel.to is auth_klass:
                    ret.append(field)
            except AttributeError:
                pass
        if len(ret) > 1:
            raise AttributeError("More than one user field in moderated model.")
        elif len(ret) == 0:
            raise AttributeError("No user field in moderated model")
        return getattr(obj, ret[0].name)



class FlagVote(Model):
    """
    Flag votes are used to calculate how likely an object will be deleted
    automatically by the system. When the weight reaches the threshold.
    """
    created = DateTimeField(_('Date Flagged'), default=now, db_index=True)
    moderator = ForeignKey(settings.AUTH_USER_MODEL, related_name="flags", on_delete=CASCADE)

    target = ForeignKey(FlagObject, related_name="votes", on_delete=CASCADE)
    weight = IntegerField(default=1)
    notes = TextField(validators=[MaxLengthValidator(1024)], **NULL)

    objects = FlagManager()

    is_censured = property(lambda self: self.weight == FlagObject.MODERATOR_CENSURE)
    is_approved = property(lambda self: self.weight == FlagObject.MODERATOR_APPROVAL)
    is_undecided = property(lambda self: self.weight == FlagObject.MODERATOR_UNDECIDED)

    class Meta:
        ordering = ('-created',)
        get_latest_by = 'created'
        permissions = (
            ("can_moderate", "User can moderate flagged content."),
        )

    def __str__(self):
        return "%s of %s by %s" % (self.weight, str(self.target), str(self.moderator))

    def weight_icon(self):
        """Return an image useful for the log"""
        key = FlagObject.FLAGS.get(self.weight, 'unknown_flag')
        name = "images/moderation/%s.svg" % key
        return storage.staticfiles_storage.url(name)

    def weight_label(self):
        """Return a standard label for the flag"""
        return FlagObject.FLAGS.get(self.weight, '_unknown').split('_')[-1].title()


from django.dispatch import receiver
@receiver(signals.post_delete)
def object_deleted(sender, instance, **kwargs):
    """Clean up any flag objects left dangling."""
    if not isinstance(instance.pk, int):
        return
    FlagObject.objects.filter(
        resolution__isnull=True,
        object_id=instance.pk,
        content_type=ContentType.objects.get_for_model(sender),
    ).update(resolution=False)


