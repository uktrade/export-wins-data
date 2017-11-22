# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-08 13:08
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


forward_sql = """
CREATE OR REPLACE FUNCTION get_financial_year
  (_date timestamp with time zone)
  RETURNS VARCHAR(20)
  IMMUTABLE
  AS $$
  BEGIN
      IF (EXTRACT(month from _date) < 4) THEN
        RETURN ((EXTRACT(year from _date) - 1) || '-' || (EXTRACT(year from _date) - 2000))::VARCHAR(20) ;
      ELSE
        RETURN (EXTRACT(year from _date) || '-' || (EXTRACT(year from _date) + 1 - 2000))::VARCHAR(20) ;
      END IF;
  END;
  $$ LANGUAGE plpgsql;

CREATE INDEX IF NOT EXISTS idx_csvfiles_file_fy ON csvfiles_file (get_financial_year(report_date));
"""

reverse_sql = """
DROP INDEX idx_csvfiles_file_fy CASCADE;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('csvfiles', '0002_auto_20171106_1524'),
    ]

    operations = [
        migrations.RunSQL(forward_sql, reverse_sql=reverse_sql),
        migrations.AlterField(
            model_name='file',
            name='file_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Export Wins'), (2, 'FDI Investments Monthly'), (3, 'FDI Investments Daily'), (
                4, 'Service Deliveries Monthly'), (5, 'Service Deliveries Daily'), (6, 'Contacts'), (7, 'Companies')]),
        ),
        migrations.AlterField(
            model_name='file',
            name='report_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='file',
            name='s3_path',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='file',
            name='user',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]