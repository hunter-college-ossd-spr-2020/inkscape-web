# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0015_auto_20170107_2355'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='team',
            options={'ordering': ('order',)},
        ),
        migrations.AddField(
            model_name='team',
            name='order',
            field=models.IntegerField(default=0),
        ),
    ]
