# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0018_auto_20170817_2250'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='auto_expire',
            field=models.IntegerField(default=0, help_text='Number of days that members are allowed to be a member.'),
        ),
    ]
