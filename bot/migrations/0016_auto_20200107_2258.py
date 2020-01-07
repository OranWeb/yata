# Generated by Django 3.0.1 on 2020-01-07 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0015_guild_stockalerts'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='guild',
            name='chainChannel',
        ),
        migrations.AddField(
            model_name='guild',
            name='allowedChannels',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='guild',
            name='allowedRoles',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
    ]
