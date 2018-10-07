# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0019_team_auto_expire'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='email',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='enrole',
            field=models.CharField(default='O', max_length=1, verbose_name='Enrollment', choices=[('O', 'Open'), ('P', 'Peer Approval'), ('T', 'Admin Approval'), ('C', 'Closed'), ('S', 'Secret'), ('E', 'Elected')]),
        ),
    ]
