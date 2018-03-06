# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0018_auto_20180306_1419'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='release',
            name='codename',
        ),
    ]
