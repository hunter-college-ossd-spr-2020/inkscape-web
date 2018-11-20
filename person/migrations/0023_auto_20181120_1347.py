# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-20 13:47
from __future__ import unicode_literals

import django.contrib.auth.validators
from django.db import migrations, models
import person.models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0022_auto_20180324_1620'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', person.models.PersonManager()),
            ],
        ),
        migrations.AlterField(
            model_name='teamchatroom',
            name='language',
            field=models.CharField(choices=[('ar', 'Arabic'), ('en', 'English'), ('de', 'German'), ('fr', 'French'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('ja', 'Japanese'), ('zh', 'Simplified Chinese'), ('zh-hant', 'Traditional Chinese'), ('ko', 'Korean')], default='en', max_length=5),
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
    ]
