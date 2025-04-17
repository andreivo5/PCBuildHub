from django.shortcuts import render, redirect, get_object_or_404
from .models import PCBuild
import random
import string
from builder.compatibility import estimate_total_power
from django.contrib.auth.decorators import login_required

def generate_short_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

def create_build(request):
    build_id = request.session.get("current_build")
    if build_id:
        try:
            return redirect("view_build", build_id=build_id)
        except PCBuild.DoesNotExist:
            del request.session["current_build"]

    short_id = generate_short_id()
    while PCBuild.objects.filter(id=short_id).exists():
        short_id = generate_short_id()

    new_build = PCBuild.objects.create(id=short_id)
    if request.user.is_authenticated:
        new_build.owner = request.user
        new_build.save()
    else:
        guest = request.session.get("guest_builds", [])
        if new_build.id not in guest:
            guest.append(new_build.id)
            request.session["guest_builds"] = guest
    request.session['current_build'] = str(new_build.id)
    return redirect(new_build.get_absolute_url())

def view_build(request, build_id):
    try:
        build = PCBuild.objects.get(id=build_id)
    except PCBuild.DoesNotExist:
        if 'current_build' in request.session:
            del request.session['current_build']
        return redirect('create_build')

    request.session['current_build'] = str(build.id)

    total_power_draw = estimate_total_power(build)
    psu_power = build.psu.power if build.psu else None

    power_status = 'normal'
    if psu_power:
        usage_ratio = total_power_draw / psu_power
        if usage_ratio > 1:
            power_status = 'danger'
        elif usage_ratio > 0.9:
            power_status = 'warning'

    components = [
        build.cpu, build.gpu, build.motherboard, build.ram,
        build.storage, build.case, build.psu, build.cooler
    ]

    def get_first_offer_url(component):
        try:
            return component.offers[0]['url'] if component and component.offers else None
        except (KeyError, IndexError, TypeError):
            return None
        
    buy_links = {
        'cpu_link': get_first_offer_url(build.cpu),
        'gpu_link': get_first_offer_url(build.gpu),
        'motherboard_link': get_first_offer_url(build.motherboard),
        'ram_link': get_first_offer_url(build.ram),
        'storage_link': get_first_offer_url(build.storage),
        'case_link': get_first_offer_url(build.case),
        'psu_link': get_first_offer_url(build.psu),
        'cooler_link': get_first_offer_url(build.cooler),
    }

    total_price = sum(c.min_price for c in components if c and c.min_price)

    context = {
        'build': build,
        'total_power_draw': total_power_draw,
        'power_status': power_status,
        'total_price': total_price,
        **buy_links
    }
    return render(request, 'create.html', context)

def new_build(request):
    if 'current_build' in request.session:
        del request.session['current_build']
    return redirect('create_build')

@login_required
def save_build(request, build_id):
    if request.method == "POST":
        build = get_object_or_404(PCBuild, id=build_id)
        build.owner = request.user
        build.save()
    return redirect("login:profile")

@login_required
def rename_build(request, build_id):
    build = get_object_or_404(PCBuild, id=build_id, owner=request.user)
    if request.method == "POST":
        new_name = request.POST.get("name", "").strip() or "Untitled Build"
        build.name = new_name
        build.save()
    return redirect("view_build", build_id=build.id)

@login_required
def delete_build(request, build_id):
    build = get_object_or_404(PCBuild, id=build_id, owner=request.user)
    if request.method == "POST":
        build.delete()
        return redirect("login:profile")
    return redirect("login:profile")