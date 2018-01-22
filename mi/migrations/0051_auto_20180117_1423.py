# Generated by Django 2.0.1 on 2018-01-17 14:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mi', '0050_auto_20171127_1548'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='csvfile',
            name='user',
        ),
        migrations.AlterField(
            model_name='overseasregiongroupyear',
            name='financial_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='mi.FinancialYear'),
        ),
        migrations.AlterField(
            model_name='overseasregiongroupyear',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='mi.OverseasRegionGroup'),
        ),
        migrations.AlterField(
            model_name='overseasregiongroupyear',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='mi.OverseasRegion'),
        ),
        migrations.AlterField(
            model_name='overseasregionyear',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='mi.Country'),
        ),
        migrations.AlterField(
            model_name='overseasregionyear',
            name='financial_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='mi.FinancialYear'),
        ),
        migrations.AlterField(
            model_name='overseasregionyear',
            name='overseas_region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='mi.OverseasRegion'),
        ),
        migrations.AlterField(
            model_name='parentsector',
            name='sector_team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='parent_sectors', to='mi.SectorTeam'),
        ),
        migrations.AlterField(
            model_name='target',
            name='financial_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='targets', to='mi.FinancialYear'),
        ),
        migrations.AlterField(
            model_name='target',
            name='hvc_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='targets', to='mi.HVCGroup'),
        ),
        migrations.AlterField(
            model_name='targetcountry',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='mi.Country'),
        ),
        migrations.AlterField(
            model_name='targetcountry',
            name='target',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='mi.Target'),
        ),
        migrations.AlterField(
            model_name='ukregiontarget',
            name='financial_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='volume_targets', to='mi.FinancialYear'),
        ),
        migrations.DeleteModel(
            name='CSVFile',
        ),
    ]
