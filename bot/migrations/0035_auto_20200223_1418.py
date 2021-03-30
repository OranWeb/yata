# Generated by Django 3.0.1 on 2020-02-23 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0034_auto_20200220_1200'),
    ]

    operations = [
        migrations.AddField(
            model_name='guild',
            name='welcomeMessage',
            field=models.BooleanField(default=True, help_text='The bot sends a welcome message in the system channel.'),
        ),
        migrations.AddField(
            model_name='guild',
            name='welcomeMessageText',
            field=models.TextField(default='', help_text='Welcome message automatically starts with "Welcome @member." Then it appends what you put here. You can put #channel and @role in plain text they\'ll be mentionned if they exist. If you put nothing it will just say "Welcome @member."'),
        ),
    ]
