# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-05 16:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mi', '0046_auto_20170905_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='targetcountry',
            name='contributes_to_target',
            field=models.BooleanField(default=False),
        ),
    ]
