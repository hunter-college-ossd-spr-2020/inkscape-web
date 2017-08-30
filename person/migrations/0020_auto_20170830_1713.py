# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0019_team_auto_expire'),
    ]

    operations = [
        migrations.AddField(
            model_name='teammembership',
            name='email',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='enrole',
            field=models.CharField(default=b'O', max_length=1, verbose_name='Enrollment', choices=[(b'O', 'Open'), (b'P', 'Peer Approval'), (b'T', 'Admin Approval'), (b'C', 'Closed'), (b'S', 'Secret'), (b'E', 'Elected')]),
        ),
    ]
