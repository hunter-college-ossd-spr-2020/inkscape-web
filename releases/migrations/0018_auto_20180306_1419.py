# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def _forwards(apps, schema_editor):
    Release = apps.get_model("releases", "Release")
    for item in Release.objects.all():
        (par, dat) = (item.parent, item.release_date)
        pre = par and dat and (not par.release_date or par.release_date > dat)
        if pre or 'pre' in item.version or 'pre' in item.codename:
            item.is_prerelease = True
            item.save()

def _backwards(*args):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0017_release_is_prerelease'),
    ]

    operations = [
        migrations.RunPython(_forwards, _backwards),
    ]
