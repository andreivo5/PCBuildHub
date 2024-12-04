from django.db import models

class CPU(models.Model):
    cpu_name = models.CharField(max_length=255)
    cores = models.IntegerField()
    cpu_mark = models.IntegerField()
    thread_mark = models.IntegerField(null=True, blank=True)
    tdp = models.IntegerField(null=True, blank=True)
    socket = models.CharField(max_length=255)
    category = models.CharField(max_length=255)

    class Meta:
        verbose_name = "CPU"
        verbose_name_plural = "CPUs"

    def __str__(self):
        return self.cpu_name

class GPU(models.Model):
    gpu_name = models.CharField(max_length=255)
    g3d_mark = models.IntegerField()
    g2d_mark = models.IntegerField()
    tdp = models.IntegerField(null=True, blank=True)
    vram = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=255)

    class Meta:
        verbose_name = "GPU"
        verbose_name_plural = "GPUs"

    def __str__(self):
        return self.gpu_name
