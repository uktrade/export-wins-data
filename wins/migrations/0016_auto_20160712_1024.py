# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-12 10:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wins', '0015_customerresponse_agree_with_win'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advisor',
            name='location',
            field=models.CharField(blank=True, max_length=128, verbose_name='Location (if applicable)'),
        ),
    ]