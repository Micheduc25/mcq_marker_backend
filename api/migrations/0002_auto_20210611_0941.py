# Generated by Django 3.2.3 on 2021-06-11 08:41

from django.db import migrations, models
import django_mysql.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='correctAnswers',
            field=django_mysql.models.ListCharField(models.CharField(max_length=3), default=['1'], max_length=100, size=None),
        ),
        migrations.AddField(
            model_name='quiz',
            name='marksAllocation',
            field=django_mysql.models.ListCharField(models.CharField(max_length=3), default=['2'], max_length=100, size=None),
        ),
        migrations.AddField(
            model_name='quiz',
            name='remarks',
            field=django_mysql.models.ListTextField(models.CharField(max_length=255), default=['courage'], max_length=100, size=None),
        ),
    ]
