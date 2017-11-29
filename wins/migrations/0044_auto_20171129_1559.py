# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-29 15:59
from __future__ import unicode_literals

from django.db import migrations

forward_sql = """
CREATE OR REPLACE VIEW wins_completed_wins_fy
    AS

    SELECT * FROM wins_win 
    WHERE 
        wins_win.is_active = True 
        AND (wins_win.total_expected_export_value > 0 OR wins_win.total_expected_non_export_value > 0 OR wins_win.total_expected_odi_value > 0) 
        AND (EXISTS(SELECT U0.id FROM wins_notification U0 WHERE (U0.is_active = True AND U0.win_id = wins_win.id AND U0.type = 'c')) OR wins_win.complete = True)
        AND (NOT EXISTS(SELECT U1.id FROM wins_customerresponse U1 WHERE (U1.is_active = True AND U1.win_id = wins_win.id))
                OR (SELECT U1.created FROM wins_customerresponse U1 WHERE (U1.is_active = True AND U1.win_id = wins_win.id) ORDER BY U1.created DESC LIMIT 1) >= get_financial_year_start())
"""

reverse_sql = """
DROP VIEW wins_completed_wins_fy CASCADE;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('wins', '0043_auto_20171117_1338'),
    ]

    operations = [
        migrations.RunSQL(forward_sql, reverse_sql),
    ]
