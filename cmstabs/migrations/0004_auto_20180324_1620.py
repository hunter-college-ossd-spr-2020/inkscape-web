# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import inkscape.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cmstabs', '0003_auto_20170107_2355'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupphotoplugin',
            name='cmsplugin_ptr',
            field=models.OneToOneField(parent_link=True, related_name='cmstabs_groupphotoplugin', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin'),
        ),
        migrations.AlterField(
            model_name='groupphotoplugin',
            name='style',
            field=models.CharField(max_length=1, verbose_name='Display Style', choices=[('L', 'Simple List'), ('P', 'Photo Heads'), ('B', 'Photo Bios'), ('0', 'Random Sponsor'), ('1', 'Full View Sponsors'), ('2', 'Icon Only Sponsors'), ('3', 'Link Only Sponsors')]),
        ),
        migrations.AlterField(
            model_name='inlinepage',
            name='cmsplugin_ptr',
            field=models.OneToOneField(parent_link=True, related_name='cmstabs_inlinepage', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin'),
        ),
        migrations.AlterField(
            model_name='inlinepages',
            name='cmsplugin_ptr',
            field=models.OneToOneField(parent_link=True, related_name='cmstabs_inlinepages', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin'),
        ),
        migrations.AlterField(
            model_name='shieldplugin',
            name='cmsplugin_ptr',
            field=models.OneToOneField(parent_link=True, related_name='cmstabs_shieldplugin', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin'),
        ),
        migrations.AlterField(
            model_name='tabcategory',
            name='icon',
            field=inkscape.fields.ResizedImageField(format='PNG', upload_to='shields/icons', max_height=32, min_height=0, max_width=32, min_width=0, verbose_name='Icon'),
        ),
    ]
