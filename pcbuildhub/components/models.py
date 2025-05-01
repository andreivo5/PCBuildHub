from django.db import models
from django.contrib.postgres.fields import JSONField

class CPU(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name")
    core_count = models.IntegerField(verbose_name="Core Count")
    core_clock = models.FloatField(null=True, blank=True, verbose_name="Base Clock (GHz)")
    boost_clock = models.FloatField(null=True, blank=True, verbose_name="Boost Clock (GHz)")
    tdp = models.IntegerField(null=True, blank=True, verbose_name="TDP (W)")
    graphics = models.CharField(max_length=100, null=True, blank=True, verbose_name="Integrated Graphics")
    smt = models.BooleanField(default=False, verbose_name="Simultaneous Multithreading (SMT)")
    brand = models.CharField(max_length=50, verbose_name="Brand")
    series = models.CharField(max_length=100, null=True, blank=True, verbose_name="Series")
    model = models.CharField(max_length=100, verbose_name="Model")
    cpu_mark = models.IntegerField(null=True, blank=True, verbose_name="PassMark CPU Mark")
    thread_mark = models.IntegerField(null=True, blank=True, verbose_name="PassMark Thread Mark")
    socket = models.CharField(max_length=100, verbose_name="Socket")
    offers = models.JSONField(null=True, blank=True)
    image = models.URLField(max_length=500, null=True, blank=True)

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
    name = models.CharField(max_length=255, verbose_name="Name")
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    brand = models.CharField(max_length=50, verbose_name="Brand")
    model = models.CharField(max_length=100, verbose_name="Model")
    vram = models.IntegerField(verbose_name="VRAM (GB)")
    g3d_mark = models.FloatField(null=True, blank=True, verbose_name="PassMark G3D Mark")
    g2d_mark = models.FloatField(null=True, blank=True, verbose_name="PassMark G2D Mark")
    tdp = models.IntegerField(null=True, blank=True, verbose_name="TDP (W)")
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
    size = models.CharField(max_length=50, verbose_name="Case Size")
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
    name = models.CharField(max_length=255, verbose_name="Name")
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    type = models.CharField(max_length=50, verbose_name="Cooler Type")
    product_code = models.CharField(max_length=50, null=True, blank=True, verbose_name="Product Code")
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
    name = models.CharField(max_length=255, verbose_name="Name")
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    type = models.CharField(max_length=50, verbose_name="RAM Type")
    size = models.IntegerField(verbose_name="Size (GB)")
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
    name = models.CharField(max_length=255, verbose_name="Name")
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    brand = models.CharField(max_length=50, verbose_name="Brand")
    socket = models.CharField(max_length=50, verbose_name="Socket")
    size = models.CharField(max_length=50, verbose_name="Form Factor")
    ram_slots = models.CharField(max_length=255, null=True, blank=True, verbose_name="RAM Slots")
    ram_type = models.CharField(max_length=10, null=True, blank=True, verbose_name="RAM Type")
    product_code = models.CharField(max_length=100, null=True, blank=True, verbose_name="Product Code")
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
    name = models.CharField(max_length=255, verbose_name="Name")
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    power = models.IntegerField(verbose_name="Wattage (W)")
    size = models.CharField(max_length=50, verbose_name="Form Factor")
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
    name = models.CharField(max_length=255, verbose_name="Name")
    image = models.URLField(max_length=500, null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    type = models.CharField(max_length=50, verbose_name="Storage Type")
    space = models.IntegerField(verbose_name="Capacity (GB)")
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
