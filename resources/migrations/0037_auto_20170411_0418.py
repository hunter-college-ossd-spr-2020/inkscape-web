# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0036_auto_20170316_1158'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='resource',
            options={'get_latest_by': 'created', 'permissions': (('can_curate', 'User can curate resources.'),)},
        ),
        migrations.AlterField(
            model_name='license',
            name='replaced',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='Replaced by', blank=True, to='resources.License', null=True),
        ),
        migrations.AlterField(
            model_name='resource',
            name='license',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='License', blank=True, to='resources.License', null=True),
        ),
    ]
