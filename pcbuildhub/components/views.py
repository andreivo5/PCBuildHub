from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import CPU, GPU, Case, Cooler, RAM, Motherboard, PSU, Storage
from builder.models import PCBuild
from builder.compatibility import case_compatibility, psu_compatibility

def components_page(request):
    return render(request, 'components.html')

def component_list(request, component_type, build_id=None, component_id=None):
    model_mapping = {
        'cpu': CPU,
        'gpu': GPU,
        'motherboard': Motherboard,
        'ram': RAM,
        'storage': Storage,
        'case': Case,
        'psu': PSU,
        'cooler': Cooler
    }

    display_names = {
        'cpu': 'CPUs',
        'gpu': 'GPUs',
        'motherboard': 'Motherboards',
        'ram': 'RAM',
        'storage': 'Storage',
        'case': 'Cases',
        'psu': 'PSUs',
        'cooler': 'CPU Coolers'
    }

    if component_type not in model_mapping:
        return render(request, '404.html')

    model = model_mapping[component_type]

    if build_id and component_id:
        build = get_object_or_404(PCBuild, id=build_id)
        component = get_object_or_404(model, id=component_id)
        setattr(build, component_type, component)
        build.save()
        return redirect(build.get_absolute_url())

    build = get_object_or_404(PCBuild, id=build_id) if build_id else None

    # Compatibility filtering:
    # CPU - Motherboard by socket
    if component_type == 'motherboard' and build and build.cpu:
        socket = build.cpu.socket
        components = model.objects.filter(socket=socket)
    elif component_type == 'cpu' and build and build.motherboard:
        socket = build.motherboard.socket
        components = model.objects.filter(socket=socket)
    else:
        components = model.objects.all()

    # Motherboard - Case by size
    if component_type == 'case' and build and build.motherboard:
        motherboard_size = build.motherboard.size
        compatible_sizes = [case_size for case_size, fits in case_compatibility.items() if motherboard_size in fits]
        components = components.filter(size__in=compatible_sizes)
    elif component_type == 'motherboard' and build and build.case:
        case_size = build.case.size
        compatible_sizes = case_compatibility.get(case_size, [])
        components = components.filter(size__in=compatible_sizes)

    # PSU - Case by size
    if component_type == 'psu' and build and build.case:
        case_size = build.case.size
        compatible_psu_sizes = psu_compatibility.get(case_size, [])
        components = components.filter(size__in=compatible_psu_sizes)

    elif component_type == 'case' and build and build.psu:
        psu_size = build.psu.size
        compatible_case_sizes = [case for case, psus in psu_compatibility.items() if psu_size in psus]
        components = components.filter(size__in=compatible_case_sizes)

    paginator = Paginator(components, 100)
    page_number = request.GET.get('page')
    components = paginator.get_page(page_number)

    return render(request, 'component_list.html', {
        'components': components,
        'component_name': component_type.capitalize(),
        'component_display_name': display_names[component_type],
        'build': build
    })

