# Generated by Django 5.1.2 on 2024-10-27 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_alter_userquestionstats_telegram_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='userquestionstats',
            name='last_incorrect',
            field=models.IntegerField(default=0),
        ),
    ]