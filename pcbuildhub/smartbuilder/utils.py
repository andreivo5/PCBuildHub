import random
import string
from builder.compatibility import case_compatibility, psu_compatibility

# Function to convert resolution and framerate to a synergy label for the ML models.
def map_label(resolution, framerate):
    res = resolution.lower()
   
    try:
        f_val = int(framerate)
        if f_val <= 60:
            return f"{res}_60"
        elif f_val < 144:
            return f"{res}_120-144"
        else:
            return f"{res}_144+"
    except:
        return f"{res}_{framerate}"

# Function to generate a short ID for builds
def generate_short_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Function to safely extract minimum price from each component
def get_min_price(component):

    try:
        val = float(component.min_price)
        return val if val > 0 else 999999
    except:
        return 999999

# Function built from properties inside builder.compatibility to ensure compatibility between components.
def compatibility_filter(qs, component_type, build):
    if not build:
        return qs

    # CPU - Motherboard
    if component_type == 'motherboard' and build.cpu:
        qs = qs.filter(socket=build.cpu.socket)
    elif component_type == 'cpu' and build.motherboard:
        qs = qs.filter(socket=build.motherboard.socket)

    # Motherboard - Case
    if component_type == 'case' and build.motherboard:
        mobo_size = build.motherboard.size
        compat_sizes = [sz for sz, fits in case_compatibility.items() if mobo_size in fits]
        qs = qs.filter(size__in=compat_sizes)
    elif component_type == 'motherboard' and build.case:
        case_size = build.case.size
        compat_sizes = case_compatibility.get(case_size, [])
        qs = qs.filter(size__in=compat_sizes)

    # PSU - Case
    if component_type == 'psu' and build.case:
        case_size = build.case.size
        psu_sizes = psu_compatibility.get(case_size, [])
        qs = qs.filter(size__in=psu_sizes)
    elif component_type == 'case' and build.psu:
        psu_size = build.psu.size
        compat_case_sizes = [c for c, p in psu_compatibility.items() if psu_size in p]
        qs = qs.filter(size__in=compat_case_sizes)

    # RAM - Motherboard
    if component_type == 'ram' and build.motherboard and build.motherboard.ram_type:
        qs = qs.filter(type__iexact=build.motherboard.ram_type)
    elif component_type == 'motherboard' and build.ram:
        qs = qs.filter(ram_type__iexact=build.ram.type)

    return qs