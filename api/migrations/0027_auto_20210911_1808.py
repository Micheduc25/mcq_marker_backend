# Generated by Django 3.2.3 on 2021-09-11 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_alter_student_sheet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='total_mark',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='results',
            name='mark',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='results',
            name='total',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='studentquestions',
            name='mark',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='studentquestions',
            name='percentage_pass',
            field=models.FloatField(),
        ),
    ]