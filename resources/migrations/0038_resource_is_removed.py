# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0037_auto_20170411_0418'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='is_removed',
            field=models.BooleanField(default=False, help_text='When checked, resource is removed from view by moderator.'),
        ),
    ]
