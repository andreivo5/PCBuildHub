from django.shortcuts import render
from main.models import CPU, GPU

def main_page(request):
    cpus = CPU.objects.all()
    gpus = GPU.objects.all()

    return render(request, 'home.html', {'cpus': cpus, 'gpus': gpus})

