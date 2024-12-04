from django.contrib import admin
from .models import CPU, GPU

@admin.register(CPU)
class CPUAdmin(admin.ModelAdmin):
    list_display = ('cpu_name', 'cores', 'cpu_mark', 'thread_mark', 'tdp', 'socket', 'category')

@admin.register(GPU)
class GPUAdmin(admin.ModelAdmin):
    list_display = ('gpu_name', 'g3d_mark', 'g2d_mark', 'tdp', 'vram', 'category')
