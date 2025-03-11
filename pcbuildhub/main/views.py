from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from main.models import CPU, GPU, Case, Cooler, RAM, Motherboard, PSU, Storage, PCBuild

def main_page(request):
    return render(request, 'home.html')

def create_build(request):
    new_build = PCBuild.objects.create()
    return render(request, 'create.html', {'build': new_build})

def view_build(request, build_id):
    build = get_object_or_404(PCBuild, id=build_id)
    return render(request, 'create.html', {'build': build})

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

    if component_type not in model_mapping:
        return render(request, '404.html')

    model = model_mapping[component_type]

    if build_id and component_id:
        build = get_object_or_404(PCBuild, id=build_id)
        component = get_object_or_404(model, id=component_id)

        setattr(build, component_type, component)
        build.save()

        return redirect(build.get_absolute_url())

    components = model.objects.all()
    per_page = request.GET.get('per_page', 100)

    if per_page != "All":
        per_page = int(per_page)
        paginator = Paginator(components, per_page)
        page_number = request.GET.get('page')
        components = paginator.get_page(page_number)

    build = get_object_or_404(PCBuild, id=build_id) if build_id else None

    return render(request, 'component_list.html', {
        'components': components,
        'component_name': component_type.capitalize(),
        'build': build,
        'per_page': per_page
    })

