# Generated by Django 3.2.3 on 2021-09-11 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0028_results_correction_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='results',
            name='session',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='studentquestions',
            name='session',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]