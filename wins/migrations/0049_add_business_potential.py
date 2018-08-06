# Generated by Django 2.0.6 on 2018-06-21 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wins', '0048_update_experience_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='win',
            name='business_potential',
            field=models.PositiveIntegerField(choices=[(1, 'The company is a medium-sized business or an exporter with high potential'), (2, 'The company exhibits characteristics of a medium-sized business or an exporter with high potential but does not meet the formal definition'), (3, 'The company is not a medium-sized business or an exporter with high potential')], blank=True, null=True, verbose_name='Medium-sized and high potential companies'),
        ),
    ]