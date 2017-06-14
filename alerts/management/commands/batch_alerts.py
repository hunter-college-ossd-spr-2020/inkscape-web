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
Sync all configured mailing lists and insert into forums.
"""

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _

from alerts.models import UserAlert, UserAlertSetting

class Command(BaseCommand):
    help = "Batches all messages into one email for users with those settings"
    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            action='store',
            dest='mode',
            default='D',
            help='Name of the mode, either "D", "W" or "M"')
        return parser

    def handle(self, mode="D", **kw):
        # We first combine all the batch settings of the same type.
        # So user 5 with alert types 2 and 18 both set to D (daily)
        # will be batched together in the second step.
        settings = defaultdict(list)
        for user_id, alert_id in UserAlertSetting.objects\
                .filter(batch=mode, email=True)\
                .values_list('user_id', 'alert_id'):
            settings[user_id].append(alert_id)

        for user_id, alert_ids in settings.items():
            UserAlert.objects.filter(
                viewed__isnull=True, # Not Viewed
                deleted__isnull=True, # Not Deleted
            ).send_batch_email(
                batch_mode=mode,
                user_id=user_id, # Belong to this user
                alert_ids=alert_ids, # For this type
            )


