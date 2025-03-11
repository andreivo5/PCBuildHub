from django.db import models
import uuid

class PCBuild(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    name = models.CharField(max_length=255, default="Untitled Build")
    cpu = models.ForeignKey('CPU', on_delete=models.SET_NULL, null=True, blank=True)
    gpu = models.ForeignKey('GPU', on_delete=models.SET_NULL, null=True, blank=True)
    motherboard = models.ForeignKey('Motherboard', on_delete=models.SET_NULL, null=True, blank=True)
    ram = models.ForeignKey('RAM', on_delete=models.SET_NULL, null=True, blank=True)
    storage = models.ForeignKey('Storage', on_delete=models.SET_NULL, null=True, blank=True)
    case = models.ForeignKey('Case', on_delete=models.SET_NULL, null=True, blank=True)
    psu = models.ForeignKey('PSU', on_delete=models.SET_NULL, null=True, blank=True)
    cooler = models.ForeignKey('Cooler', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return f"/create/{self.id}/"

    def __str__(self):
        return f"Build {self.id}"

class CPU(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)  
    url = models.URLField(max_length=500, null=True, blank=True)  
    brand = models.CharField(max_length=50)  
    socket = models.CharField(max_length=100)  
    speed = models.FloatField(null=True, blank=True)  
    core_count = models.IntegerField()  
    thread_count = models.IntegerField()  
    series = models.CharField(max_length=100, null=True, blank=True) 
    model = models.CharField(max_length=100)  
    cpu_mark = models.IntegerField(null=True, blank=True)  
    thread_mark = models.IntegerField(null=True, blank=True) 
    tdp = models.IntegerField(null=True, blank=True)  

    class Meta:
        verbose_name = "CPU"
        verbose_name_plural = "CPUs"

    def __str__(self):
        return self.name

class GPU(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    brand = models.CharField(max_length=50)
    vram = models.IntegerField()
    resolution = models.CharField(max_length=50, null=True, blank=True)
    model = models.CharField(max_length=100)
    vram_gb = models.IntegerField()
    g3d_mark = models.FloatField(null=True, blank=True)
    g2d_mark = models.FloatField(null=True, blank=True)
    tdp = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "GPU"
        verbose_name_plural = "GPUs"

    def __str__(self):
        return self.name
    
class Case(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    size = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Case"
        verbose_name_plural = "Cases"

    def __str__(self):
        return self.name

class Cooler(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    type = models.CharField(max_length=50)

    class Meta:
        verbose_name = "CPU Cooler"
        verbose_name_plural = "CPU Coolers"

    def __str__(self):
        return self.name

class RAM(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    type = models.CharField(max_length=50)
    size = models.IntegerField()

    class Meta:
        verbose_name = "RAM"
        verbose_name_plural = "RAM Modules"

    def __str__(self):
        return self.name

class Motherboard(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    brand = models.CharField(max_length=50)
    socket = models.CharField(max_length=50)
    size = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Motherboard"
        verbose_name_plural = "Motherboards"

    def __str__(self):
        return self.name

class PSU(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    power = models.IntegerField()
    size = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Power Supply"
        verbose_name_plural = "Power Supplies"

    def __str__(self):
        return self.name
    
class Storage(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    type = models.CharField(max_length=50)
    space = models.IntegerField()

    class Meta:
        verbose_name = "Storage"
        verbose_name_plural = "Storage Devices"

    def __str__(self):
        return self.name