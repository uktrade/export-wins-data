# Generated by Django 2.0.8 on 2018-11-02 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_mi_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='sso_user_id',
            field=models.UUIDField(null=True, unique=True),
        ),
    ]