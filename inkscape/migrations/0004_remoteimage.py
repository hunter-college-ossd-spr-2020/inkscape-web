# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import inkscape.utils


class Migration(migrations.Migration):

    dependencies = [
        ('inkscape', '0003_heartbeat'),
    ]

    operations = [
        migrations.CreateModel(
            name='RemoteImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('md5_prefix', models.CharField(max_length=16, null=True, blank=True)),
                ('local_file', models.FileField(storage=inkscape.utils.ReplaceStore(), null=True, upload_to='remote', blank=True)),
                ('remote_url', models.URLField()),
            ],
        ),
    ]
