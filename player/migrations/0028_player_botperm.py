# Generated by Django 2.2.7 on 2019-12-11 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0027_playerdata_ipsban'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='botPerm',
            field=models.BooleanField(default=False),
        ),
    ]
