from django.db.models import Q

# File used for filters on the component pages, work in progress.

def apply_filters(component_type, queryset, request):
    brand = request.GET.get('brand')
    socket = request.GET.get('socket')
    ram_type = request.GET.get('ram_type')
    size = request.GET.get('size')
    type_ = request.GET.get('type')
    vram = request.GET.get('vram')
    power = request.GET.get('power')

    if brand:
        queryset = queryset.filter(brand__iexact=brand)

    if component_type in ['cpu', 'motherboard'] and socket:
        queryset = queryset.filter(socket__iexact=socket)

    if component_type == 'ram' and ram_type:
        queryset = queryset.filter(type__iexact=ram_type)
    elif component_type == 'motherboard' and ram_type:
        queryset = queryset.filter(ram_type__iexact=ram_type)

    if component_type in ['motherboard', 'case', 'psu'] and size:
        queryset = queryset.filter(size__iexact=size)

    if component_type == 'storage' and type_:
        queryset = queryset.filter(type__iexact=type_)

    if component_type == 'gpu' and vram:
        queryset = queryset.filter(vram__iexact=vram)

    if component_type == 'psu' and power:
        queryset = queryset.filter(power__gte=power)

    return queryset


def apply_sorting(component_type, queryset, request):
    sort = request.GET.get('sort')

    valid_sorts = {
        'cpu': ['price', '-price', 'cpu_mark', '-cpu_mark', 'core_count', '-core_count', 'tdp', '-tdp', 'speed', '-speed'],
        'gpu': ['price', '-price', 'g3d_mark', '-g3d_mark', 'vram', '-vram', 'tdp', '-tdp'],
        'motherboard': ['price', '-price', 'name', '-name', 'size', '-size'],
        'ram': ['price', '-price', 'size', '-size', 'type', '-type'],
        'storage': ['price', '-price', 'size', '-size', 'type', '-type'],
        'psu': ['price', '-price', 'power', '-power'],
        'case': ['price', '-price', 'size', '-size'],
        'cooler': ['price', '-price', 'name', '-name']
    }

    if sort in valid_sorts.get(component_type, []):
        queryset = queryset.order_by(sort)

    return queryset
