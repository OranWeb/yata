# Generated by Django 2.0.7 on 2020-02-07 15:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0041_auto_20200207_1528'),
    ]

    operations = [
        migrations.RenameField(
            model_name='revivesreport',
            old_name='targetsReceived',
            new_name='revivesReceived',
        ),
    ]
