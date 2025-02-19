from django.shortcuts import render
from main.models import CPU, GPU, HDD

def main_page(request):
    cpus = CPU.objects.all()
    gpus = GPU.objects.all()
    hdds = HDD.objects.all()

    return render(request, 'home.html', {'cpus': cpus, 'gpus': gpus, 'hdds': hdds})