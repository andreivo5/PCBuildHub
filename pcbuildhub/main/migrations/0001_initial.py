# Generated by Django 5.1.3 on 2025-03-06 02:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('image', models.URLField(blank=True, max_length=500, null=True)),
                ('url', models.URLField(blank=True, max_length=500, null=True)),
                ('size', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Case',
                'verbose_name_plural': 'Cases',
            },
        ),
        migrations.CreateModel(
            name='Cooler',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('image', models.URLField(blank=True, max_length=500, null=True)),
                ('url', models.URLField(blank=True, max_length=500, null=True)),
                ('type', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'CPU Cooler',
                'verbose_name_plural': 'CPU Coolers',
            },
        ),
        migrations.CreateModel(
            name='CPU',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('image', models.URLField(blank=True, max_length=500, null=True)),
                ('url', models.URLField(blank=True, max_length=500, null=True)),
                ('brand', models.CharField(max_length=50)),
                ('socket', models.CharField(max_length=100)),
                ('speed', models.FloatField(blank=True, null=True)),
                ('core_count', models.IntegerField()),
                ('thread_count', models.IntegerField()),
                ('series', models.CharField(blank=True, max_length=100, null=True)),
                ('model', models.CharField(max_length=100)),
                ('cpu_mark', models.IntegerField(blank=True, null=True)),
                ('thread_mark', models.IntegerField(blank=True, null=True)),
                ('tdp', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'CPU',
                'verbose_name_plural': 'CPUs',
            },
        ),
        migrations.CreateModel(
            name='GPU',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('image', models.URLField(blank=True, max_length=500, null=True)),
                ('url', models.URLField(blank=True, max_length=500, null=True)),
                ('brand', models.CharField(max_length=50)),
                ('vram', models.IntegerField()),
                ('resolution', models.CharField(blank=True, max_length=50, null=True)),
                ('model', models.CharField(max_length=100)),
                ('vram_gb', models.IntegerField()),
                ('g3d_mark', models.FloatField(blank=True, null=True)),
                ('g2d_mark', models.FloatField(blank=True, null=True)),
                ('tdp', models.FloatField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'GPU',
                'verbose_name_plural': 'GPUs',
            },
        ),
        migrations.CreateModel(
            name='Motherboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('image', models.URLField(blank=True, max_length=500, null=True)),
                ('url', models.URLField(blank=True, max_length=500, null=True)),
                ('brand', models.CharField(max_length=50)),
                ('socket', models.CharField(max_length=50)),
                ('size', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Motherboard',
                'verbose_name_plural': 'Motherboards',
            },
        ),
        migrations.CreateModel(
            name='PSU',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('image', models.URLField(blank=True, max_length=500, null=True)),
                ('url', models.URLField(blank=True, max_length=500, null=True)),
                ('power', models.IntegerField()),
                ('size', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Power Supply',
                'verbose_name_plural': 'Power Supplies',
            },
        ),
        migrations.CreateModel(
            name='RAM',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('image', models.URLField(blank=True, max_length=500, null=True)),
                ('url', models.URLField(blank=True, max_length=500, null=True)),
                ('type', models.CharField(max_length=50)),
                ('size', models.IntegerField()),
            ],
            options={
                'verbose_name': 'RAM',
                'verbose_name_plural': 'RAM Modules',
            },
        ),
        migrations.CreateModel(
            name='Storage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('image', models.URLField(blank=True, max_length=500, null=True)),
                ('url', models.URLField(blank=True, max_length=500, null=True)),
                ('type', models.CharField(max_length=50)),
                ('space', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Storage',
                'verbose_name_plural': 'Storage Devices',
            },
        ),
    ]
