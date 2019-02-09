# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-02-09 04:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0023_auto_20190209_0305'),
        ('cms', '0020_old_tree_cleanup'),
        ('cmstabs', '0004_auto_20180324_1620'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='cmstabs_teamplugin', serialize=False, to='cms.CMSPlugin')),
                ('template', models.CharField(choices=[('large_vert', 'Large Rows with Icon'), ('small_vert', 'Small Text Only Rows'), ('large_horz', 'Large Icons Only'), ('small_horz', 'Links Only')], default='small_horz', max_length=32)),
                ('role', models.ForeignKey(blank=True, help_text='Limit to just this role.', null=True, on_delete=django.db.models.deletion.CASCADE, to='person.MembershipRole')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Team')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
