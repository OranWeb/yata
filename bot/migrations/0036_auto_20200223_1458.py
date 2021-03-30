# Generated by Django 3.0.1 on 2020-02-23 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0035_auto_20200223_1418'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guild',
            name='welcomeMessageText',
            field=models.TextField(blank=True, default='', help_text='Welcome message automatically starts with "Welcome @member." Then it appends what you put here. You can put #channel and @role in plain text they\'ll be mentionned if they exist. If you put nothing it will just say "Welcome @member."'),
        ),
    ]
