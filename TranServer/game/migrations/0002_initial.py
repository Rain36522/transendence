# Generated by Django 4.2.11 on 2024-04-14 13:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('game', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tournament', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gameuser',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='game',
            name='nextGame',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='game.game'),
        ),
        migrations.AddField(
            model_name='game',
            name='tournament',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tournament.tournament'),
        ),
    ]
