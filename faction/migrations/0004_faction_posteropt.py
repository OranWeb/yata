# Generated by Django 3.0.1 on 2020-01-27 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0003_auto_20200124_1518'),
    ]

    operations = [
        migrations.AddField(
            model_name='faction',
            name='posterOpt',
            field=models.TextField(default='{}'),
        ),
    ]
