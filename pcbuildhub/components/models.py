from django.db import models
from django.contrib.postgres.fields import JSONField

class CPU(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    brand = models.CharField(max_length=50)
    socket = models.CharField(max_length=100)
    core_count = models.IntegerField()
    core_clock = models.FloatField(null=True, blank=True)  
    boost_clock = models.FloatField(null=True, blank=True)  
    smt = models.BooleanField(default=False)
    graphics = models.CharField(max_length=100, null=True, blank=True)
    series = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100)
    cpu_mark = models.IntegerField(null=True, blank=True)
    thread_mark = models.IntegerField(null=True, blank=True)
    tdp = models.IntegerField(null=True, blank=True)
    offers = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "CPU"
        verbose_name_plural = "CPUs"

    def __str__(self):
        return self.name

    @property
    def thread_count(self):
        return self.core_count * 2 if self.smt else self.core_count
    
    @property
    def min_price(self):
        try:
            return min(float(o["price"]) for o in self.offers if "price" in o)
        except:
            return None

class GPU(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=100)
    vram = models.IntegerField() 
    resolution = models.CharField(max_length=50, null=True, blank=True)
    g3d_mark = models.FloatField(null=True, blank=True)
    g2d_mark = models.FloatField(null=True, blank=True)
    tdp = models.IntegerField(null=True, blank=True)
    offers = models.JSONField(null=True, blank=True)  

    class Meta:
        verbose_name = "GPU"
        verbose_name_plural = "GPUs"

    def __str__(self):
        return self.name
    
    @property
    def min_price(self):
        try:
            return min(float(o["price"]) for o in self.offers if "price" in o)
        except:
            return None
    
class Case(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    size = models.CharField(max_length=50)
    offers = models.JSONField(null=True, blank=True) 

    class Meta:
        verbose_name = "Case"
        verbose_name_plural = "Cases"

    def __str__(self):
        return self.name
    
    @property
    def min_price(self):
        try:
            return min(float(o["price"]) for o in self.offers if "price" in o)
        except:
            return None

class Cooler(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    type = models.CharField(max_length=50)
    product_code = models.CharField(max_length=50, null=True, blank=True)
    offers = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "CPU Cooler"
        verbose_name_plural = "CPU Coolers"

    def __str__(self):
        return self.name
    
    @property
    def min_price(self):
        try:
            return min(float(o["price"]) for o in self.offers if "price" in o)
        except:
            return None

class RAM(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    type = models.CharField(max_length=50)
    size = models.IntegerField()
    offers = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "RAM"
        verbose_name_plural = "RAM Modules"

    def __str__(self):
        return self.name
    
    @property
    def min_price(self):
        try:
            return min(float(o["price"]) for o in self.offers if "price" in o)
        except:
            return None

class Motherboard(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    brand = models.CharField(max_length=50)
    socket = models.CharField(max_length=50)
    size = models.CharField(max_length=50)
    ram_slots = models.CharField(max_length=255, null=True, blank=True)
    ram_type = models.CharField(max_length=10, null=True, blank=True)
    product_code = models.CharField(max_length=100, null=True, blank=True)  
    offers = models.JSONField(null=True, blank=True)  

    class Meta:
        verbose_name = "Motherboard"
        verbose_name_plural = "Motherboards"

    def __str__(self):
        return self.name
    
    @property
    def min_price(self):
        try:
            return min(float(o["price"]) for o in self.offers if "price" in o)
        except:
            return None

class PSU(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    power = models.IntegerField()
    size = models.CharField(max_length=50)
    offers = models.JSONField(null=True, blank=True)  

    class Meta:
        verbose_name = "Power Supply"
        verbose_name_plural = "Power Supplies"

    def __str__(self):
        return self.name
    
    @property
    def min_price(self):
        try:
            return min(float(o["price"]) for o in self.offers if "price" in o)
        except:
            return None
    
class Storage(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    type = models.CharField(max_length=50)
    space = models.IntegerField()
    offers = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Storage"
        verbose_name_plural = "Storage Devices"

    def __str__(self):
        return self.name
    
    @property
    def min_price(self):
        try:
            return min(float(o["price"]) for o in self.offers if "price" in o)
        except:
            return None
