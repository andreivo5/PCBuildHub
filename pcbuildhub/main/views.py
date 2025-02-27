from django.shortcuts import render
from main.models import CPU, GPU

def main_page(request):
    return render(request, 'home.html')

def create_build(request):
    return render(request, 'create.html')