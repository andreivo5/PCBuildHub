from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import CPU, GPU, Case, Cooler, RAM, Motherboard, PSU, Storage
from builder.models import PCBuild
from builder.compatibility import case_compatibility, psu_compatibility, estimate_total_power
from django.db.models import Q
from .filters import apply_filters, apply_sorting

def components_page(request):
    return render(request, 'components.html')

model_mapping = {
    'cpu': (CPU, 'CPU'),
    'gpu': (GPU, 'GPU'),
    'motherboard': (Motherboard, 'Motherboard'),
    'ram': (RAM, 'RAM'),
    'storage': (Storage, 'Storage'),
    'psu': (PSU, 'Power Supply'),
    'case': (Case, 'Case'),
    'cooler': (Cooler, 'CPU Cooler')
}

def get_min_offer_price(offers):
    try:
        return min(float(o['price']) for o in offers) if offers else None
    except (KeyError, ValueError, TypeError):
        return None

def component_list(request, component_type, build_id=None, component_id=None):
    
    # Pretty display names for the webpage
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

    model, _ = model_mapping[component_type]

    # Context if page is loaded as part of a current build
    if build_id and component_id:
        build = get_object_or_404(PCBuild, id=build_id)
        component = get_object_or_404(model, id=component_id)
        setattr(build, component_type, component)
        build.save()

        estimate_total_power(build)  

        request.session['current_build'] = str(build.id)
        
        return redirect(build.get_absolute_url())

    build = get_object_or_404(PCBuild, id=build_id) if build_id else None

    # Base case, no filter on components
    components = model.objects.all()

    # === Compatibility Filtering ===

    # CPU - Motherboard by socket
    if component_type == 'motherboard' and build and build.cpu:
        components = components.filter(socket=build.cpu.socket)
    elif component_type == 'cpu' and build and build.motherboard:
        components = components.filter(socket=build.motherboard.socket)

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

    # RAM - Motherboard by type
    if component_type == 'ram' and build and build.motherboard:
        components = components.filter(type__iexact=build.motherboard.ram_type)
    elif component_type == 'motherboard' and build and build.ram:
        components = components.filter(ram_type__iexact=build.ram.type)

    # === Search logic ===
    search_query = request.GET.get('search', '').strip()
    if search_query:
        components = components.filter(name__icontains=search_query)


    """
    # Apply filters and sorting
    components = apply_filters(component_type, components, request)
    components = apply_sorting(component_type, components, request)

    # Filter choices logic
    filter_choices = {}

    if component_type in ['cpu', 'gpu', 'motherboard', 'ram']:
        filter_choices['brands'] = components.values_list('brand', flat=True).distinct().order_by('brand')

    if component_type in ['cpu', 'motherboard']:
        filter_choices['sockets'] = components.values_list('socket', flat=True).distinct().order_by('socket')

    if component_type == 'motherboard':
        filter_choices['ram_types'] = components.values_list('ram_type', flat=True).distinct().order_by('ram_type')
        filter_choices['sizes'] = components.values_list('size', flat=True).distinct().order_by('size')

    if component_type == 'ram':
        filter_choices['ram_types'] = components.values_list('type', flat=True).distinct().order_by('type')
        filter_choices['sizes'] = components.values_list('size', flat=True).distinct().order_by('size')

    if component_type == 'gpu':
        filter_choices['vrams'] = components.values_list('vram', flat=True).distinct().order_by('vram')

    if component_type == 'storage':
        filter_choices['types'] = components.values_list('type', flat=True).distinct().order_by('type')
        filter_choices['sizes'] = components.values_list('size', flat=True).distinct().order_by('size')

    if component_type == 'psu':
        filter_choices['sizes'] = components.values_list('size', flat=True).distinct().order_by('size')
        filter_choices['powers'] = components.values_list('power', flat=True).distinct().order_by('power')

    if component_type == 'case':
        filter_choices['sizes'] = components.values_list('size', flat=True).distinct().order_by('size')

    if component_type == 'cooler':
        filter_choices['types'] = components.values_list('type', flat=True).distinct().order_by('type')

    """

    # Minimum price logic
    for c in components:
        c.min_price = get_min_offer_price(getattr(c, 'offers', None))

    # Pagination logic
    paginator = Paginator(components, 30)
    product_count = components.count()
    page_number = request.GET.get('page')
    components = paginator.get_page(page_number)

    # Context for rendering below
    context = {
        'components': components,
        'component_name': component_type.capitalize(),
        'component_display_name': display_names[component_type],
        'build': build,
        'product_count': product_count,
        #'filters': request.GET,
        #'filter_choices': filter_choices
    }

    return render(request, 'component_list.html', context)

def component_detail(request, component_type, component_id, build_id=None):
    if component_type not in model_mapping:
        return render(request, '404.html')

    build = get_object_or_404(PCBuild, id=build_id) if build_id else None
    model, display_name = model_mapping[component_type]
    component = get_object_or_404(model, id=component_id)

    # Build a spec dictionary from all fields except ID and image/url
    exclude_fields = ['id', 'name', 'image', 'url', 'offers']
    specs = {
        field.verbose_name.title(): getattr(component, field.name)
        for field in model._meta.fields
        if field.name not in exclude_fields
    }

    return render(request, 'component_detail.html', {
        'component': component,
        'component_type': component_type,
        'display_name': display_name,
        'specs': specs,
        'build': build,
        'offers': getattr(component, 'offers', []),
    })
