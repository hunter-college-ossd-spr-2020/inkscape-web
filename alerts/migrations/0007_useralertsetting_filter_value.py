# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0006_auto_20170107_2355'),
    ]

    operations = [
        migrations.AddField(
            model_name='useralertsetting',
            name='filter_value',
            field=models.CharField(help_text='An extra filter variable which can be different for each alert.', max_length=255, null=True, blank=True),
        ),
    ]
