# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-05 10:46
from __future__ import unicode_literals

from django.db import migrations

from wins.constants import HQ_TEAM_REGION_OR_POST
region_to_itt = {
    'East Midlands': 'itt:DIT Team East Midlands - International Trade Team',
    'East of England': 'itt:DIT Team East',
    'London': 'itt:London International Trade Team',
    'North East': 'itt:DIT North East Regional International Trade Office',
    'North West': 'itt:The North West International Trade Team',
    'South East': 'itt:DIT Team South East - International Trade Team',
    'South West': 'itt:DIT South West',
    'Yorkshire and The Humber': 'itt:DIT Yorkshire',
}
location_to_itt = {
    'ingham': 'itt:DIT Team West Midlands - Birmingham',
    'black': 'itt:DIT Team West Midlands - Black Country',
    'coventry': 'itt:DIT Team West Midlands - Coventry',
    'inter': 'itt:DIT Team West Midlands - Coventry',
    'inta': 'itt:DIT Team West Midlands - Coventry',
    'intra': 'itt:DIT Team West Midlands - Coventry',
    'wolv': 'itt:DIT West Midlands Team - Regional Team',
    'heref': 'itt:DIT Team West Midlands - Hereford and Worcester',
    'plymouth': 'itt:DIT South West',
    'bristol': 'itt:DIT South West',
    'burton': 'itt:DIT Team West Midlands - Staffordshire',
    'stafford': 'itt:DIT Team West Midlands - Staffordshire',
    'shrop': 'itt:DIT Team West Midlands - Shropshire',
}

def thing(obj):
    obj.team_type = 'itt'
    hq_team_display = obj.get_hq_team_display()
    itt = region_to_itt.get(hq_team_display)
    if itt:
        print(hq_team_display, obj.location, itt)
    elif hq_team_display == 'West Midlands':
        loc = obj.location.lower()
        for location_snippet, loc_itt in location_to_itt.items():
            if location_snippet in loc:
                itt = loc_itt
                print(hq_team_display, obj.location, itt)
                break
        else:
            itt = 'itt:DIT West Midlands Team - Regional Team'
            print('!!! MISC !!!', hq_team_display, obj.location, itt)
    else:
        assert False, '{} {}'.format(hq_team_display, 'not found')
    assert itt in set(dict(HQ_TEAM_REGION_OR_POST)), 'itt not found {}'.format(itt)
    obj.hq_team = itt
    obj.save()

def update(apps, schema_editor):
    Win = apps.get_model('wins', 'Win')
    Advisor = apps.get_model('wins', 'Advisor')
    for win in Win.objects.filter(team_type='region'):
        thing(win)
    for ad in Advisor.objects.filter(team_type='region'):
        thing(ad)


class Migration(migrations.Migration):

    dependencies = [
        ('wins', '0023_auto_20160824_1123'),
    ]

    operations = [
        migrations.RunPython(update),
    ]