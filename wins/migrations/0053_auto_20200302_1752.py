# Generated by Django 2.2.10 on 2020-03-02 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wins', '0052_deletedwin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customerresponse',
            name='other_marketing_source',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='Other marketing source'),
        ),
    ]
