from django.contrib import admin
from .models import CPU, GPU, HDD

@admin.register(CPU)
class CPUAdmin(admin.ModelAdmin):
    list_display = ('cpu_name', 'cores', 'cpu_mark', 'thread_mark', 'tdp', 'socket', 'category')

@admin.register(GPU)
class GPUAdmin(admin.ModelAdmin):
    list_display = ('gpu_name', 'g3d_mark', 'g2d_mark', 'tdp', 'vram', 'category')

@admin.register(HDD)
class HDDAdmin(admin.ModelAdmin):
    list_display = ('drive_name', 'size', 'disk_mark', 'type')
