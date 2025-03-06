from django.shortcuts import render
from django.core.paginator import Paginator
from main.models import CPU, GPU, Case, Cooler, RAM, Motherboard, PSU, Storage

def main_page(request):
    return render(request, 'home.html')

def create_build(request):
    return render(request, 'create.html')

def components_page(request):
    return render(request, 'components.html')

def cpu_list(request):
    per_page = request.GET.get('per_page', 100)
    if per_page == 'All':
        cpus = CPU.objects.all()
    else:
        per_page = int(per_page)
        cpus = CPU.objects.all()
        paginator = Paginator(cpus, per_page)
        page_number = request.GET.get('page')
        cpus = paginator.get_page(page_number)

    return render(request, 'cpu_list.html', {'cpus': cpus, 'per_page': per_page})

def gpu_list(request):
    per_page = request.GET.get('per_page', 100)
    if per_page == 'All':
        gpus = GPU.objects.all()
    else:
        per_page = int(per_page)
        gpus = GPU.objects.all()
        paginator = Paginator(gpus, per_page)
        page_number = request.GET.get('page')
        gpus = paginator.get_page(page_number)

    return render(request, 'gpu_list.html', {'gpus': gpus, 'per_page': per_page})

def case_list(request):
    per_page = request.GET.get('per_page', 100)
    if per_page == 'All':
        cases = Case.objects.all()
    else:
        per_page = int(per_page)
        cases = Case.objects.all()
        paginator = Paginator(cases, per_page)
        page_number = request.GET.get('page')
        cases = paginator.get_page(page_number)

    return render(request, 'case_list.html', {'cases': cases, 'per_page': per_page})

def cooler_list(request):
    per_page = request.GET.get('per_page', 100)
    if per_page == 'All':
        coolers = Cooler.objects.all()
    else:
        per_page = int(per_page)
        coolers = Cooler.objects.all()
        paginator = Paginator(coolers, per_page)
        page_number = request.GET.get('page')
        coolers = paginator.get_page(page_number)

    return render(request, 'cooler_list.html', {'coolers': coolers, 'per_page': per_page})

def ram_list(request):
    per_page = request.GET.get('per_page', 100)
    if per_page == 'All':
        rams = RAM.objects.all()
    else:
        per_page = int(per_page)
        rams = RAM.objects.all()
        paginator = Paginator(rams, per_page)
        page_number = request.GET.get('page')
        rams = paginator.get_page(page_number)

    return render(request, 'ram_list.html', {'rams': rams, 'per_page': per_page})

def motherboard_list(request):
    per_page = request.GET.get('per_page', 100)
    if per_page == 'All':
        motherboards = Motherboard.objects.all()
    else:
        per_page = int(per_page)
        motherboards = Motherboard.objects.all()
        paginator = Paginator(motherboards, per_page)
        page_number = request.GET.get('page')
        motherboards = paginator.get_page(page_number)

    return render(request, 'motherboard_list.html', {'motherboards': motherboards, 'per_page': per_page})

def psu_list(request):
    per_page = request.GET.get('per_page', 100)
    if per_page == 'All':
        psus = PSU.objects.all()
    else:
        per_page = int(per_page)
        psus = PSU.objects.all()
        paginator = Paginator(psus, per_page)
        page_number = request.GET.get('page')
        psus = paginator.get_page(page_number)

    return render(request, 'psu_list.html', {'psus': psus, 'per_page': per_page})

def storage_list(request):
    per_page = request.GET.get('per_page', 100)
    if per_page == 'All':
        storages = Storage.objects.all()
    else:
        per_page = int(per_page)
        storages = Storage.objects.all()
        paginator = Paginator(storages, per_page)
        page_number = request.GET.get('page')
        storages = paginator.get_page(page_number)

    return render(request, 'storage_list.html', {'storages': storages, 'per_page': per_page})



