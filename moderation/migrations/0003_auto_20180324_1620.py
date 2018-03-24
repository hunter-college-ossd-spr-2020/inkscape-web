# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moderation', '0002_auto_20170410_1750'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='flagvote',
            options={'ordering': ('-created',), 'get_latest_by': 'created', 'permissions': (('can_moderate', 'User can moderate flagged content.'),)},
        ),
    ]
