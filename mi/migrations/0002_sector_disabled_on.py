# Generated by Django 2.2.10 on 2020-06-04 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mi', '0001_squashed_0052_add_unknown_uk_region_target'),
    ]

    operations = [
        migrations.AddField(
            model_name='sector',
            name='disabled_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sector',
            name='name',
            field=models.CharField(max_length=256),
        ),
    ]
