# Generated by Django 3.0.4 on 2020-04-02 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0080_attacksreport_fill'),
    ]

    operations = [
        migrations.AddField(
            model_name='chain',
            name='respectComputed',
            field=models.FloatField(default=0),
        ),
    ]
