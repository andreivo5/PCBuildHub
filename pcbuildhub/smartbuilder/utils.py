import random, string
from django.http import HttpResponse
from django.shortcuts import redirect
from builder.compatibility import estimate_total_power
from builder.models import CPU, GPU, Motherboard, RAM, Storage, PSU, Case, Cooler, PCBuild
from .recovery import budget_recovery
from .logging_config import logger
from .helpers import get_min_price, compatibility_filter, price_ok

# Function to map user inputs to model labels.
def map_label(use_case, resolution=None, framerate=None, software=None, dev_type=None):
    if use_case == "gaming":
        framerate = framerate.replace("–", "-").replace("—", "-")
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

    elif use_case == "editing":
        res = resolution.lower()
        sw = software.lower()
        if "premiere" in sw:
            return f"edit_{res}_premiere"
        elif "resolve" in sw:
            return f"edit_{res}_resolve"
        else:
            return f"edit_{res}_other"

    elif use_case == "dev":
        if not dev_type:
            raise ValueError("Missing 'dev_type' for development use case.")
        
        dev_map = {
            "web": "web",
            "mobile": "mobile",
            "game": "game",
            "data science": "datasci"
        }

        dev_type_normalized = dev_map.get(dev_type.lower())
        if not dev_type_normalized:
            raise ValueError(f"Invalid dev_type: {dev_type}")
        
        return f"dev_{dev_type_normalized}"

    else:
        raise ValueError(f"Unknown use case: {use_case}")

# Function to generate a short ID for builds
def generate_short_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))



def select_cpu_for_casual(inputs, budget):
    cpus = CPU.objects.exclude(cpu_mark__isnull=True)

    for cpu in cpus:
        if get_min_price(cpu) <= budget * 0.4 and price_ok(cpu):
            return cpu

    if inputs["use"] == "multitasking":
        cpus = cpus.filter(cpu_mark__gte=12000, core_count__gte=6)
    else:
        cpus = cpus.filter(cpu_mark__gte=8000)

    cpus = sorted(cpus, key=get_min_price)

    for cpu in cpus:
        if get_min_price(cpu) <= budget * 0.4:
            return cpu

    return cpus[0] if cpus else None

def select_gpu_for_casual(inputs, cpu):
    gpus = GPU.objects.exclude(g3d_mark__isnull=True)
    if inputs["use"] == "multitasking":
        filtered = [
            gpu for gpu in gpus
            if gpu.g3d_mark >= 10000 and get_min_price(gpu) <= 400 and price_ok(gpu)
        ]
        filtered = sorted(filtered, key=get_min_price)
        if filtered:
            mid_index = len(filtered) // 2
            return filtered[mid_index]

    filtered = [
        gpu for gpu in gpus
        if (gpu.g3d_mark <= 10000 or get_min_price(gpu) <= 200) and price_ok(gpu)
    ]
    filtered = sorted(filtered, key=get_min_price)
    if filtered:
        mid_index = len(filtered) // 2
        return filtered[mid_index]

    fallback = sorted([g for g in gpus if price_ok(g)], key=get_min_price)
    return fallback[len(fallback) // 2] if fallback else None

def finish_smart_builder_flow(request, cpu, gpu, numeric_budget, use_case, resolution, casual_inputs):
    prefer_ddr5 = numeric_budget > 1500 or use_case in ["editing", "dev"]
    mobos = Motherboard.objects.filter(socket=cpu.socket)

    if use_case == "casual":
        ddr4_mobos = mobos.filter(ram_type__icontains="DDR4")
        if ddr4_mobos.exists():
            mobos = ddr4_mobos
        else:
            logger.info("No DDR4 boards found for casual use, falling back to DDR5.")
    elif prefer_ddr5:
        ddr5_mobos = mobos.filter(ram_type__icontains="DDR5")
        if ddr5_mobos.exists():
            mobos = ddr5_mobos

    motherboard_candidates = sorted(mobos, key=get_min_price, reverse=True)
    if not motherboard_candidates:
        return HttpResponse("No compatible motherboards found.", status=404)
    chosen_mobo = motherboard_candidates[0]

    if numeric_budget <= 1000:
        max_ram_price = 60
    elif numeric_budget <= 2000:
        max_ram_price = 90
    elif numeric_budget <= 3000:
        max_ram_price = 150
    else:
        max_ram_price = float('inf')

    if numeric_budget <= 1000:
        max_storage_price = 80
    elif numeric_budget <= 2000:
        max_storage_price = 120
    elif numeric_budget <= 3000:
        max_storage_price = 200
    else:
        max_storage_price = float('inf')

    if use_case == "casual":
        if casual_inputs["tabs"] == "many" or casual_inputs["use"] == "multitasking":
            ram_sizes = [32, 16]
        elif casual_inputs["tabs"] == "some":
            ram_sizes = [16]
        else:
            ram_sizes = [8, 16]
    elif use_case == "dev" and ("datasci" in casual_inputs.get("label", "") or "game" in casual_inputs.get("label", "")):
        ram_sizes = [64, 32]
    elif use_case == "dev":
        ram_sizes = [32, 16]
    elif use_case == "editing":
        ram_sizes = [64, 32]
    else:
        ram_sizes = [64, 32, 16]

    ram_type_kw = "DDR5" if prefer_ddr5 else "DDR4"
    ram_candidates = []
    for size in ram_sizes:
        rams = RAM.objects.filter(type__icontains=ram_type_kw, size=size)
        filtered = compatibility_filter(rams, "ram", PCBuild(motherboard=chosen_mobo))
        filtered = [r for r in filtered if get_min_price(r) <= max_ram_price]
        ram_candidates += sorted(filtered, key=get_min_price, reverse=True)
    if not ram_candidates:
        return HttpResponse("No compatible RAM found.", status=404)
    chosen_ram = ram_candidates[0]

    if use_case == "casual":
        if casual_inputs["storage"] == "a lot":
            storage_sizes = [2000, 1000]
            storage_types = ["SATA", "NVME"]
        elif casual_inputs["storage"] == "some":
            storage_sizes = [1000, 500]
            storage_types = ["NVME", "SATA"]
        else:
            storage_sizes = [500, 256]
            storage_types = ["NVME", "SATA"]
    elif use_case == "editing" or (use_case == "dev" and ("datasci" in casual_inputs.get("label", "") or "game" in casual_inputs.get("label", ""))):
        storage_sizes = [2000, 1000, 500]
        storage_types = ["NVME", "SATA"]
    else:
        storage_sizes = [1000, 500]
        storage_types = ["NVME", "SATA"]

    storage_candidates = []
    for size in storage_sizes:
        for stype in storage_types:
            options = Storage.objects.filter(space__gte=size, type__icontains=stype)
            filtered = [s for s in options if get_min_price(s) <= max_storage_price]
            storage_candidates += sorted(filtered, key=get_min_price, reverse=True)
    if not storage_candidates:
        return HttpResponse("No suitable storage found.", status=404)
    chosen_storage = storage_candidates[0]

    partial_build = PCBuild(
        cpu=cpu, gpu=gpu, motherboard=chosen_mobo,
        ram=chosen_ram, storage=chosen_storage
    )
    resolution_is_high = resolution.lower() in ["1440p", "4k"] or use_case in ["editing", "dev"]
    headroom = 1.5 if resolution_is_high else 1.3
    needed_wattage = int(estimate_total_power(partial_build) * headroom)
    psus = PSU.objects.filter(power__gte=needed_wattage)
    psu_candidates = sorted(psus, key=get_min_price, reverse=True)
    if not psu_candidates:
        return HttpResponse("No PSU found.", status=404)
    chosen_psu = psu_candidates[len(psu_candidates) // 2]

    partial_build.psu = chosen_psu
    case_qs = compatibility_filter(Case.objects.all(), "case", partial_build)
    if use_case == "casual" and casual_inputs["size_pref"] == "quiet/compact":
        case_qs = case_qs.filter(size__in=["ITX", "mATX"])
    case_candidates = sorted(case_qs, key=get_min_price, reverse=True)
    if not case_candidates:
        return HttpResponse("No compatible case found.", status=404)
    chosen_case = case_candidates[0]

    cooler_candidates = []
    if use_case == "casual" and casual_inputs["size_pref"] == "quiet/compact":
        coolers = Cooler.objects.filter(type__iexact="air")
        cooler_candidates = sorted(coolers, key=get_min_price, reverse=True)
    else:
        for ctype in ["liquid", "air"]:
            coolers = Cooler.objects.filter(type__iexact=ctype)
            cooler_candidates += sorted(coolers, key=get_min_price, reverse=True)
    if not cooler_candidates:
        return HttpResponse("No cooler found.", status=404)
    chosen_cooler = cooler_candidates[len(cooler_candidates) // 2]

    components = [cpu, gpu, chosen_mobo, chosen_ram, chosen_storage, chosen_psu, chosen_case, chosen_cooler]
    total_price = sum(get_min_price(c) for c in components if c)

    logger.debug("- Initial Build - over budget:")
    for c in components:
        if c:
            logger.debug(f"  - {type(c).__name__}: {c.name} (EUR{get_min_price(c):.2f})")
        else:
            logger.debug("  - Missing component in build!")
    logger.debug(f"Total: EUR{total_price:.2f} > Budget: EUR{numeric_budget}")

    recovery_candidates = {
        "motherboard": motherboard_candidates,
        "ram": ram_candidates,
        "storage": storage_candidates,
        "psu": psu_candidates,
        "case": case_candidates,
        "cooler": cooler_candidates
    }

    final_comps, final_total, success = budget_recovery(
        components, numeric_budget, partial_build, recovery_candidates, use_case
    )

    if not success or final_total > numeric_budget:
        logger.debug(f"- Budget Recovery - failed or still over budget: EUR {final_total:.2f}")
        return HttpResponse("No valid build could be recovered within budget.", status=404)
    else:
        components = final_comps
        total_price = final_total
        logger.info(f"- ACCEPTED - Post-recovery build at EUR{total_price:.2f}")

    new_build = PCBuild.objects.create(
        id=generate_short_id(),
        name="Smart Build",
        cpu=cpu,
        gpu=gpu,
        motherboard=chosen_mobo,
        ram=chosen_ram,
        storage=chosen_storage,
        psu=chosen_psu,
        case=chosen_case,
        cooler=chosen_cooler
    )

    request.session["current_build"] = str(new_build.id)
    logger.info(f"- SUCCESS - Build {new_build.id} created successfully at EUR{total_price:.2f}")
    return redirect(new_build.get_absolute_url())