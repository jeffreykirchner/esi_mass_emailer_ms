# Generated by Django 3.2 on 2021-04-11 21:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_massemail_app'),
    ]

    operations = [
        migrations.AddField(
            model_name='massemail',
            name='email_count',
            field=models.IntegerField(default=0, verbose_name='Email Count'),
        ),
    ]
