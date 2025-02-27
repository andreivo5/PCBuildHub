from django.shortcuts import render
from main.models import CPU, GPU

def main_page(request):
    return render(request, 'home.html')

def create_build(request):
    return render(request, 'create.html')

def components_page(request):
    return render(request, 'components.html')

def cpu_list(request):
    cpus = CPU.objects.all() 
    return render(request, 'cpu_list.html', {'cpus': cpus})

def gpu_list(request):
    gpus = GPU.objects.all()
    return render(request, 'gpu_list.html', {'gpus': gpus})
