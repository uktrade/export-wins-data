# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-09 12:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wins', '0006_auto_20160608_1602'),
    ]

    operations = [
        migrations.AlterField(
            model_name='win',
            name='has_hvo_specialist_involvement',
            field=models.BooleanField(verbose_name='Have HVO Specialists been involved?'),
        ),
        migrations.AlterField(
            model_name='win',
            name='is_line_manager_confirmed',
            field=models.BooleanField(verbose_name='My line manager has confirmed the decision to record this win'),
        ),
        migrations.AlterField(
            model_name='win',
            name='is_prosperity_fund_related',
            field=models.BooleanField(verbose_name='Is this win prosperity fund related?'),
        ),
    ]
