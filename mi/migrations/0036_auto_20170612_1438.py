# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-12 14:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mi', '0040_auto_20170612_1012'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='target',
            name='country',
        ),
        migrations.AddField(
            model_name='target',
            name='country',
            field=models.ManyToManyField(related_name='targets', to='mi.Country'),
        ),
    ]