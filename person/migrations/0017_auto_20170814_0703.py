# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import inkscape.fields


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0016_auto_20170507_2352'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamMembership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('requested', models.DateTimeField(null=True, blank=True)),
                ('joined', models.DateTimeField(null=True, blank=True)),
                ('expired', models.DateTimeField(null=True, blank=True)),
                ('title', models.CharField(max_length=128, null=True, verbose_name='Role Title', blank=True)),
                ('style', models.CharField(max_length=64, null=True, verbose_name='Role Style', blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='team',
            name='requests',
        ),
        migrations.RemoveField(
            model_name='team',
            name='watchers',
        ),
        migrations.AlterField(
            model_name='team',
            name='group',
            field=inkscape.fields.AutoOneToOneField(related_name='team', to='auth.Group'),
        ),
        migrations.AlterField(
            model_name='user',
            name='photo',
            field=inkscape.fields.ResizedImageField(format=b'PNG', upload_to=b'photos', max_width=190, min_height=0, max_height=190, blank=True, min_width=0, null=True, verbose_name='Photograph (square)'),
        ),
        migrations.AddField(
            model_name='teammembership',
            name='added_by',
            field=models.ForeignKey(related_name='has_added_users', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='teammembership',
            name='removed_by',
            field=models.ForeignKey(related_name='has_removed_users', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='teammembership',
            name='team',
            field=models.ForeignKey(related_name='memberships', to='person.Team'),
        ),
        migrations.AddField(
            model_name='teammembership',
            name='user',
            field=models.ForeignKey(related_name='memberships', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='teammembership',
            unique_together=set([('team', 'user')]),
        ),
    ]
