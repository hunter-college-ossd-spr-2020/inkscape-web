# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-02-09 03:05
from __future__ import unicode_literals

import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import person.models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0022_auto_20180324_1620'),
    ]

    operations = [
        migrations.CreateModel(
            name='MembershipRole',
            fields=[
                ('code', models.SlugField(help_text="The simple lowercase 'slug' that is used in urls (unique for whole website).", max_length=12, primary_key=True, serialize=False, verbose_name='Role URL Code')),
                ('title', models.CharField(max_length=128, verbose_name='Role Title')),
                ('style', models.CharField(blank=True, choices=[('plat', 'Platinum'), ('winner', 'Gold'), ('grey', 'Silver'), ('orange', 'Bronze'), ('purple', 'Purple'), ('blue', 'Blue'), ('red', 'Red'), ('green', 'Green')], max_length=64, null=True, verbose_name='Role Style')),
                ('number', models.IntegerField(default=0, help_text='If greater than zero, will limit the number of this role to this count.', verbose_name='Maximum number')),
                ('public', models.BooleanField(default=True, help_text='If set to false, this role can only be selected by team admins.', verbose_name='Publically Choosable')),
            ],
        ),
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', person.models.PersonManager()),
            ],
        ),
        migrations.AddField(
            model_name='team',
            name='enrole_msg',
            field=models.TextField(blank=True, help_text='This message is displayed to users requesting to join the team.', null=True, verbose_name='Enrolement Message'),
        ),
        migrations.AlterField(
            model_name='teamchatroom',
            name='channel',
            field=models.CharField(max_length=64, verbose_name='Chatroom Name'),
        ),
        migrations.AlterField(
            model_name='teamchatroom',
            name='language',
            field=models.CharField(choices=[('ar', 'Arabic'), ('en', 'English'), ('de', 'German'), ('fr', 'French'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('ja', 'Japanese'), ('zh', 'Simplified Chinese'), ('zh-hant', 'Traditional Chinese'), ('ko', 'Korean')], default='en', max_length=5),
        ),
        migrations.AlterField(
            model_name='teammembership',
            name='style',
            field=models.CharField(blank=True, choices=[('plat', 'Platinum'), ('winner', 'Gold'), ('grey', 'Silver'), ('orange', 'Bronze'), ('purple', 'Purple'), ('blue', 'Blue'), ('red', 'Red'), ('green', 'Green')], max_length=64, null=True, verbose_name='Custom Role Style'),
        ),
        migrations.AlterField(
            model_name='teammembership',
            name='title',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='Custom Role Title'),
        ),
        migrations.AlterField(
            model_name='user',
            name='language',
            field=models.CharField(blank=True, choices=[('ar', 'Arabic'), ('en', 'English'), ('de', 'German'), ('fr', 'French'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('ja', 'Japanese'), ('zh', 'Simplified Chinese'), ('zh-hant', 'Traditional Chinese'), ('ko', 'Korean')], max_length=8, null=True, verbose_name='Default Language'),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username'),
        ),
        migrations.AddField(
            model_name='membershiprole',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mtypes', to='person.Team'),
        ),
        migrations.AddField(
            model_name='teammembership',
            name='role',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='person.MembershipRole'),
        ),
    ]