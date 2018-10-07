# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import inkscape.fields


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0003_auto_20160126_1557'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='platform',
            options={'ordering': ('codename',)},
        ),
        migrations.AddField(
            model_name='release',
            name='background',
            field=inkscape.fields.ResizedImageField(format='PNG', upload_to='release/background', max_width=960, min_height=0, max_height=300, blank=True, min_width=0, null=True),
            preserve_default=True,
        ),
    ]
