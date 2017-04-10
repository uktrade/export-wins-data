# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-04-05 13:11
from __future__ import unicode_literals
import datetime

from django.db import migrations


def do_thing(apps, schema_editor):
    # change all existing hvc fields to have the FY encoded at the end
    Win = apps.get_model('wins', 'Win')
    for win in Win.objects.all():
        if not win.hvc:
            continue
        fy = "16" if win.date < datetime.date(2017, 4, 1) else "17"
        win.hvc = win.hvc + fy
        win.save()


class Migration(migrations.Migration):

    dependencies = [
        ('wins', '0040_auto_20170404_0456'),
    ]

    operations = [
        migrations.RunPython(do_thing),
    ]