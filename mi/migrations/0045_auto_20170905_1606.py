# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-05 16:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mi', '0044_auto_20170904_1011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='target',
            name='hvc_group',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, related_name='targets', to='mi.HVCGroup'),
        ),
    ]
