# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0021_user_website'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='charter',
            field=models.TextField(blank=True, help_text='HTML page with rules for team members.', null=True, verbose_name='Charter', validators=[django.core.validators.MaxLengthValidator(30240)]),
        ),
        migrations.AlterField(
            model_name='team',
            name='desc',
            field=models.TextField(blank=True, help_text='HTML description on the teams front page.', null=True, verbose_name='Full Description', validators=[django.core.validators.MaxLengthValidator(10240)]),
        ),
        migrations.AlterField(
            model_name='team',
            name='intro',
            field=models.TextField(blank=True, help_text='Text inside the team introduction.', null=True, verbose_name='Introduction', validators=[django.core.validators.MaxLengthValidator(1024)]),
        ),
        migrations.AlterField(
            model_name='team',
            name='side_bar',
            field=models.TextField(blank=True, help_text='Extra sie bar for buttons and useful links.', null=True, verbose_name='Side Bar', validators=[django.core.validators.MaxLengthValidator(10240)]),
        ),
    ]
