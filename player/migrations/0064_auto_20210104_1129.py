# Generated by Django 3.1.2 on 2021-01-04 11:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0063_auto_20201119_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='section',
            field=models.CharField(choices=[('*', 'all'), ('B', 'bazaar'), ('F', 'faction'), ('T', 'target'), ('A', 'awards'), ('S', 'stock'), ('C', 'company'), ('L', 'loot')], default='B', max_length=16),
        ),
    ]
