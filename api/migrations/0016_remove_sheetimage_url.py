# Generated by Django 3.2.3 on 2021-07-17 11:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_sheetimage_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sheetimage',
            name='url',
        ),
    ]