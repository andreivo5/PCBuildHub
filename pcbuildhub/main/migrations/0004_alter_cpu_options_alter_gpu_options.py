# Generated by Django 5.1.3 on 2024-12-04 02:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_alter_cpu_thread_mark'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cpu',
            options={'verbose_name': 'CPU', 'verbose_name_plural': 'CPUs'},
        ),
        migrations.AlterModelOptions(
            name='gpu',
            options={'verbose_name': 'GPU', 'verbose_name_plural': 'GPUs'},
        ),
    ]
