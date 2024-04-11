# Generated by Django 4.2.11 on 2024-04-10 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='ballwidth',
            field=models.DecimalField(decimal_places=2, default=0.1, max_digits=5),
        ),
        migrations.AlterField(
            model_name='game',
            name='planksize',
            field=models.DecimalField(decimal_places=2, default=0.3, max_digits=5),
        ),
    ]
