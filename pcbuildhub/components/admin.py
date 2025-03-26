from django.contrib import admin
from .models import CPU, GPU, Case, Cooler, RAM, Motherboard, PSU, Storage

@admin.register(CPU)
class CPUAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "series", "model", "core_count", "thread_count", "speed", "cpu_mark", "tdp")
    search_fields = ("name", "brand", "series", "model")
    list_filter = ("brand", "series", "socket")

@admin.register(GPU)
class GPUAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "model", "vram", "g3d_mark", "tdp")
    search_fields = ("name", "brand", "model")
    list_filter = ("brand", "vram_gb")

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("name", "size")
    search_fields = ("name",)
    list_filter = ("size",)

@admin.register(Cooler)
class CoolerAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    search_fields = ("name",)
    list_filter = ("type",)

@admin.register(RAM)
class RAMAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "size")
    search_fields = ("name", "type")
    list_filter = ("type", "size")

@admin.register(Motherboard)
class MotherboardAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "socket", "size")
    search_fields = ("name", "brand", "socket")
    list_filter = ("brand", "socket", "size")

@admin.register(PSU)
class PSUAdmin(admin.ModelAdmin):
    list_display = ("name", "power", "size")
    search_fields = ("name",)
    list_filter = ("power", "size")

@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "space")
    search_fields = ("name", "type")
    list_filter = ("type", "space")
