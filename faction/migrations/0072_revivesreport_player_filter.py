# Generated by Django 3.0.1 on 2020-03-11 21:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0071_auto_20200311_1709'),
    ]

    operations = [
        migrations.AddField(
            model_name='revivesreport',
            name='player_filter',
            field=models.IntegerField(default=0),
        ),
    ]
