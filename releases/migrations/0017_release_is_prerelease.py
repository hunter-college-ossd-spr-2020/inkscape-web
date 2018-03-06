# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0016_auto_20180208_1807'),
    ]

    operations = [
        migrations.AddField(
            model_name='release',
            name='is_prerelease',
            field=models.BooleanField(default=False, help_text='If set, will indicate that this is a testing pre-release and should not be given to users.', verbose_name='is Pre-Release'),
        ),
    ]
