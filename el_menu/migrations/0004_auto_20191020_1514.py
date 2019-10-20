# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-10-20 15:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('el_menu', '0003_auto_20191010_1531'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='menutranslation',
            options={'ordering': ('language',)},
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='category',
            field=models.SlugField(blank=True, choices=[(None, 'Main Menu'), ('foot', 'Footer'), ('tab', 'Tab'), ('hidden', 'Hidden')], max_length=12, null=True),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='url',
            field=models.CharField(blank=True, help_text='Location of content.', max_length=255, null=True),
        ),
    ]
