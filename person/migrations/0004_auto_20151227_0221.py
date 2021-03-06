# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.contrib.auth.models
import inkscape.fields


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0003_auto_20160122_0915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='requests',
            field=models.ManyToManyField(related_name='team_requests', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='watchers',
            field=models.ManyToManyField(related_name='watches', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='bio',
            field=models.TextField(blank=True, null=True, validators=[django.core.validators.MaxLengthValidator(4096)]),
        ),
        migrations.AddField(
            model_name='user',
            name='dauser',
            field=models.CharField(max_length=64, null=True, verbose_name='deviantArt User', blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='gpg_key',
            field=models.TextField(blank=True, null=True, verbose_name='GPG Public Key', validators=[django.core.validators.MaxLengthValidator(262144)]),
        ),
        migrations.AddField(
            model_name='user',
            name='ircdev',
            field=models.BooleanField(default=False, verbose_name='Join Developer Channel'),
        ),
        migrations.AddField(
            model_name='user',
            name='ircnick',
            field=models.CharField(max_length=20, null=True, verbose_name='IRC Nickname', blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='ircpass',
            field=models.CharField(max_length=128, null=True, verbose_name='Freenode Password (optional)', blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='language',
            field=models.CharField(blank=True, max_length=8, null=True, verbose_name='Default Language', choices=[('en', 'English'), ('de', 'German'), ('da', 'Danish'), ('fr', 'French'), ('nl', 'Dutch'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('ja', 'Japanese'), ('zh', 'Chinese'), ('zh-tw', 'Simplified Chinese'), ('ko', 'Korean')]),
        ),
        migrations.AddField(
            model_name='user',
            name='last_seen',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='ocuser',
            field=models.CharField(max_length=64, null=True, verbose_name='openClipArt User', blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='photo',
            field=inkscape.fields.ResizedImageField(format='PNG', upload_to='photos', max_width=190, min_height=0, max_height=190, blank=True, min_width=0, null=True, verbose_name='Photograph (square)'),
        ),
        migrations.AddField(
            model_name='user',
            name='tbruser',
            field=models.CharField(max_length=64, null=True, verbose_name='Tumblr User', blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='visits',
            field=models.IntegerField(default=0),
        ),
    ]
