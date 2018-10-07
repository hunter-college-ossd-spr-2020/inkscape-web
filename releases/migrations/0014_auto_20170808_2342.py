# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import inkscape.fields


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0013_auto_20170316_1217'),
    ]

    operations = [
        migrations.AddField(
            model_name='platform',
            name='instruct',
            field=models.TextField(help_text='If supplied, this text will appear after the tabs, but before the release notes. Will propergate to all child platforms that do not have their own.', null=True, verbose_name='Instructions', blank=True),
        ),
        migrations.AlterField(
            model_name='platform',
            name='icon',
            field=inkscape.fields.ResizedImageField(format='PNG', upload_to='release/icons', max_width=32, min_height=0, max_height=32, blank=True, min_width=0, null=True),
        ),
        migrations.AlterField(
            model_name='platform',
            name='image',
            field=inkscape.fields.ResizedImageField(format='PNG', upload_to='release/icons', max_width=256, min_height=0, max_height=256, blank=True, min_width=0, null=True),
        ),
        migrations.AlterField(
            model_name='release',
            name='background',
            field=inkscape.fields.ResizedImageField(format='PNG', upload_to='release/background', max_width=960, min_height=0, max_height=360, blank=True, min_width=0, null=True),
        ),
        migrations.AlterField(
            model_name='release',
            name='release_date',
            field=models.DateField(help_text='ONLY set this when THIS release is ready to go. Set pre-release dates on pre-releases and remember, as soon as this is released, it will take over the default redirection and users will start downloading this release.', null=True, verbose_name='Release date', db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='releasestatus',
            name='icon',
            field=inkscape.fields.ResizedImageField(format='PNG', upload_to='release/icons', max_width=32, min_height=0, max_height=32, blank=True, min_width=0, null=True),
        ),
    ]
