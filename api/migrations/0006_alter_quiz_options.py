# Generated by Django 3.2.3 on 2021-06-11 12:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_quiz_remarks'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='quiz',
            options={'ordering': ['-created']},
        ),
    ]
