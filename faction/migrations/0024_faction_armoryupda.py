# Generated by Django 3.0.1 on 2020-02-02 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0023_news'),
    ]

    operations = [
        migrations.AddField(
            model_name='faction',
            name='armoryUpda',
            field=models.IntegerField(default=0),
        ),
    ]
