# Generated by Django 3.0.1 on 2020-02-03 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0032_contributors'),
    ]

    operations = [
        migrations.CreateModel(
            name='FactionData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('territoryUpda', models.IntegerField(default=0)),
                ('contrabs', models.TextField(default='[1,2,3]')),
            ],
        ),
    ]
