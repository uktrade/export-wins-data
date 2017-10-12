# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-10 10:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fdi', '0011_auto_20171004_1631'),
        ('mi', '0048_auto_20170906_0924')
    ]

    operations = [
        migrations.CreateModel(
            name='FDIGlobalTargets',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('high', models.PositiveIntegerField()),
                ('good', models.PositiveIntegerField()),
                ('standard', models.PositiveIntegerField()),
                ('financial_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mi.FinancialYear')),
            ],
        ),
    ]