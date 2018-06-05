# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0003_auto_20180324_1620'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='for_role',
            field=models.CharField(help_text='The role the elected members will have in the team.', max_length=128, null=True, blank=True),
        ),
    ]
