# Generated by Django 3.0.8 on 2020-08-01 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('target', '0020_attack_paid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='target',
            name='faction_position',
            field=models.CharField(default='faction_position', max_length=32),
        ),
    ]
