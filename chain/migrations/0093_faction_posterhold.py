# Generated by Django 3.0.1 on 2020-01-06 22:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chain', '0092_auto_20200106_1252'),
    ]

    operations = [
        migrations.AddField(
            model_name='faction',
            name='posterHold',
            field=models.BooleanField(default=False),
        ),
    ]
