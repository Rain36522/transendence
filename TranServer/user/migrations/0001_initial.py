# Generated by Django 4.2.11 on 2024-04-19 12:49

from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('username', models.CharField(max_length=255, unique=True)),
                ('token', models.CharField(blank=True, max_length=255)),
                ('mailValidate', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_active', models.DateTimeField(default=django.utils.timezone.now)),
                ('wins', models.PositiveIntegerField(default=0, verbose_name='Number of wins')),
                ('ball_color', models.CharField(default='#FFFFFF', max_length=7)),
                ('paddle_color', models.CharField(default='#FFFFFF', max_length=7)),
                ('enemy_paddle_color', models.CharField(default='#FFFFFF', max_length=7)),
                ('frame_color', models.CharField(default='#FFFFFF', max_length=7)),
                ('background_color', models.CharField(default='#000000', max_length=7)),
                ('total_games', models.PositiveIntegerField(default=0, verbose_name='Total number of games')),
                ('tournaments_wins', models.PositiveIntegerField(default=0, verbose_name='Number of tournaments wins')),
                ('total_tournaments', models.PositiveIntegerField(default=0, verbose_name='Total number of tournaments')),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_images/')),
                ('blocked', models.ManyToManyField(related_name='blocked_by', to=settings.AUTH_USER_MODEL)),
                ('friends', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('invites', models.ManyToManyField(related_name='sent_invites', to=settings.AUTH_USER_MODEL)),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
