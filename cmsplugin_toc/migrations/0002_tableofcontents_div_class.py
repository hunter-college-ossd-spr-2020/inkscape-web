# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cmsplugin_toc', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tableofcontents',
            name='div_class',
            field=models.CharField(default='right', max_length=22, verbose_name='Class', choices=[('right', 'Float Right'), ('inline', 'Inline')]),
            preserve_default=True,
        ),
    ]
