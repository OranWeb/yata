# Generated by Django 3.0.1 on 2020-01-29 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0015_chain_attacks'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wall',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tId', models.IntegerField(default=0)),
                ('tss', models.IntegerField(default=0)),
                ('tse', models.IntegerField(default=0)),
                ('attackers', models.TextField(blank=True, default='{}', null=True)),
                ('defenders', models.TextField(blank=True, default='{}', null=True)),
                ('attackerFactionId', models.IntegerField(default=0)),
                ('attackerFactionName', models.CharField(default='AttackFaction', max_length=32)),
                ('defenderFactionId', models.IntegerField(default=0)),
                ('defenderFactionName', models.CharField(default='DefendFaction', max_length=32)),
                ('territory', models.CharField(default='AAA', max_length=3)),
                ('result', models.CharField(default='Unset', max_length=10)),
                ('breakdown', models.TextField(blank=True, default='[]', null=True)),
                ('breakSingleFaction', models.BooleanField(default=False)),
                ('factions', models.ManyToManyField(blank=True, to='faction.Faction')),
            ],
        ),
    ]
