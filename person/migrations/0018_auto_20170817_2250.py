# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0017_auto_20170814_0703'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': [('use_irc', 'IRC Chat Training Complete'), ('website_cla_agreed', 'Agree to Website License'), ('is_staff', 'Staff permissions are automatically granted.')]},
        ),
    ]
