# Generated by Django 3.1.3 on 2023-03-04 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20230304_2118'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='hosteltype',
            field=models.CharField(choices=[('None', 'None'), ('AC', 'AC'), ('Non AC', 'Non AC')], default='non_ac', max_length=20, null=True),
        ),
    ]
