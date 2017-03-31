# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2017-03-08 18:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wins', '0032_hvc'),
    ]

    operations = [
        migrations.AddField(
            model_name='win',
            name='total_expected_odi_value',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='breakdown',
            name='type',
            field=models.PositiveIntegerField(choices=[(1, 'Export'), (2, 'Non-export'), (3, 'ODI')]),
        ),
    ]