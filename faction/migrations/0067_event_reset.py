# Generated by Django 3.0.1 on 2020-03-09 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0066_member_lastactionstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='reset',
            field=models.BooleanField(default=False),
        ),
    ]
