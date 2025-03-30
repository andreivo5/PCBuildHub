from django.db import models
from components.models import CPU, GPU, RAM, Motherboard, PSU, Cooler, Case, Storage

class PCBuild(models.Model):
    id = models.CharField(max_length=6, primary_key=True, unique=True)
    name = models.CharField(max_length=255, default="Untitled Build")
    cpu = models.ForeignKey(CPU, on_delete=models.SET_NULL, null=True, blank=True)
    gpu = models.ForeignKey(GPU, on_delete=models.SET_NULL, null=True, blank=True)
    motherboard = models.ForeignKey(Motherboard, on_delete=models.SET_NULL, null=True, blank=True)
    ram = models.ForeignKey(RAM, on_delete=models.SET_NULL, null=True, blank=True)
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL, null=True, blank=True)
    case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True)
    psu = models.ForeignKey(PSU, on_delete=models.SET_NULL, null=True, blank=True)
    cooler = models.ForeignKey(Cooler, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return f"/create/{self.id}/"

    def __str__(self):
        return f"Build {self.id}"
