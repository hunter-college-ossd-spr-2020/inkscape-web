# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0014_resourcerevision_revisionmanager'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RevisionManager',
        ),
        migrations.AddField(
            model_name='gallery',
            name='desc',
            field=models.TextField(blank=True, null=True, verbose_name='Description', validators=[django.core.validators.MaxLengthValidator(50192)]),
        ),
        migrations.AddField(
            model_name='gallery',
            name='status',
            field=models.CharField(blank=True, max_length=1, null=True, db_index=True, choices=[(None, 'No Status'), (' ', 'Casual Wish'), ('1', 'Draft'), ('2', 'Proposal'), ('3', 'Reviewed Proposal'), ('+', 'Under Development'), ('=', 'Complete'), ('-', 'Rejected')]),
        ),
        migrations.AddField(
            model_name='gallery',
            name='thumbnail',
            field=models.ForeignKey(blank=True, to='resources.Resource', help_text='Which resource should be the thumbnail for this gallery', null=True),
        ),
    ]
