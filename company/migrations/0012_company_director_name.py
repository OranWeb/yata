# Generated by Django 3.1.2 on 2020-11-18 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0011_auto_20201118_0831'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='director_name',
            field=models.CharField(default='Player', max_length=16),
        ),
    ]
