# Generated by Django 3.0.1 on 2020-03-23 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0072_revivesreport_player_filter'),
    ]

    operations = [
        migrations.AddField(
            model_name='chain',
            name='shareId',
            field=models.SlugField(blank=True, default='', max_length=32, null=True),
        ),
    ]
