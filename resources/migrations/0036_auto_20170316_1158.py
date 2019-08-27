# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import resources.storage


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0035_auto_20170130_0041'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='download',
            field=models.FileField(storage=resources.storage.ResourceStorage(), upload_to='resources/file', null=True, verbose_name='Consumable File', blank=True),
        ),
    ]
