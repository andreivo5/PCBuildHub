from django.shortcuts import render, redirect
from django.http import HttpResponse

from builder.models import CPU, GPU, Motherboard, RAM, Storage, PSU, Case, Cooler, PCBuild
from builder.compatibility import estimate_total_power
from .recommender.predict import predict_cpu_gpu_synergy
from .recovery import budget_recovery
from .utils import map_label, generate_short_id, get_min_price, compatibility_filter
from .logging_config import logger

def smart_builder_home(request):
    return render(request, 'smartbuild.html', {
        'use_cases': ["Gaming", "Video Editing", "Development", "Casual"],
        'gaming_resolutions': ["1080p", "1440p", "4K"],
        'gaming_framerates': ["60", "120–144", "144+"],
        'editing_resolutions': ["1080p", "4K"],
        'editing_software': ["Premiere Pro", "DaVinci Resolve", "Other"],
        'dev_types': ["Web", "Mobile", "Game", "Data Science"],
        'casual_primary_use': ["Web & media", "Light creative work", "Multitasking"],
        'casual_tabs': ["Few", "Some", "Many"],
        'casual_storage': ["Minimal", "Some", "A lot"],
        'casual_size_pref': ["Quiet/Compact", "No preference"],
        'budgets': [
            {"label": "<€1000", "value": "1000"},
            {"label": "€1000–€2000", "value": "2000"},
            {"label": "€2000–€3000", "value": "3000"},
            {"label": "€3000–€5000", "value": "5000"},
            {"label": "€5000+", "value": "999999"},
        ]
    })

def smart_builder_submit(request):
    if request.method != "POST":
        return redirect("smart_builder_home")

    resolution = request.POST.get("resolution", "1080p")
    framerate = request.POST.get("framerate", "60")
    numeric_budget = int(request.POST.get("budget", 2000))
    synergy_label = map_label(resolution, framerate)

    logger.info(f"SmartBuilder: Resolution={resolution}, FPS={framerate}, Label={synergy_label}, Budget={numeric_budget}")

    # (Step 1): GPU & CPU gathering, deduplicating GPUs by model, using lowest price option.
    raw_gpus = GPU.objects.exclude(g3d_mark__isnull=True)
    gpu_models = {}

    for g in raw_gpus:
        if not g.model:
            continue
        current = gpu_models.get(g.model)
        if not current or get_min_price(g) < get_min_price(current):
            gpu_models[g.model] = g

    unique_gpus = list(gpu_models.values())
    raw_cpus = CPU.objects.exclude(cpu_mark__isnull=True)

    # (Step 2): Evaluating synergy using recommender models for every CPU & GPU pair, storing combos.
    synergy_threshold = 0.9
    combos = []
    for gpu in unique_gpus:
        for cpu in raw_cpus:
            # Early price check to filter out components w/ value over budget x 0.7
            gpu_price = get_min_price(gpu)
            cpu_price = get_min_price(cpu)
            if gpu_price + cpu_price > numeric_budget * 0.7:
                logger.debug(f"- Rejected - CPU + GPU combo due to price: CPU={cpu.name} (EUR {cpu_price:.2f}), GPU={gpu.name} (EUR {gpu_price:.2f})")
                continue

            synergy_score = predict_cpu_gpu_synergy(synergy_label, cpu, gpu)
            logger.debug(f"- Synergy Check - CPU={cpu.name}, GPU={gpu.name}, Score={synergy_score:.3f}")
            if synergy_score >= synergy_threshold:
                combos.append((cpu, gpu, synergy_score))

    if not combos:
        logger.warning("No CPU/GPU synergy combos found by model.")
        return HttpResponse("No synergy combos found for these requirements.", status=404)

    # Sorting combos by synergy descending.
    combos.sort(key=lambda x: x[2], reverse=True)
    logger.info(f"- Found: {len(combos)} synergy combos. Trying them in descending synergy order.")

    # (Step 3) Iterating combos, building out the rest of the PC each time by budget checking.
    for (candidate_cpu, candidate_gpu_repr, synergy_val) in combos:
        logger.debug(
            f"- Trying Synergy - CPU ={candidate_cpu.name} (EUR{get_min_price(candidate_cpu):.2f}), "
            f"- GPU ={candidate_gpu_repr.name} (EUR{get_min_price(candidate_gpu_repr):.2f}), "
            f"- Synergy ={synergy_val:.3f}"
        )

        # (Step 3a): GPU recheck - picking the cheapest sub-brand GPU with the same model, failsafe to logic in step 1.
        same_model_gpus = GPU.objects.filter(model=candidate_gpu_repr.model)
        cheapest_subbrand_gpu = None
        cheapest_price = 999999
        for g in same_model_gpus:
            mp = get_min_price(g)
            if mp < cheapest_price:
                cheapest_price = mp
                cheapest_subbrand_gpu = g

        chosen_gpu = cheapest_subbrand_gpu or candidate_gpu_repr
        chosen_cpu = candidate_cpu

        # (Step 3b): Motherboard, sorting by most expensive first
        prefer_ddr5 = numeric_budget > 1500
        mobos = Motherboard.objects.filter(socket=chosen_cpu.socket)
        if prefer_ddr5:
            ddr5_mobos = mobos.filter(ram_type__icontains="DDR5")
            if ddr5_mobos.exists():
                mobos = ddr5_mobos
        motherboard_candidates = sorted(mobos, key=get_min_price, reverse=True)
        if not motherboard_candidates:
            logger.warning("- NOT FOUND - Motherboards. Skipping this synergy.")
            continue
        chosen_mobo = motherboard_candidates[0]

        # (Step 3c): RAM with set preferences per budget
        if numeric_budget <= 1000:
            max_ram_price = 60
        elif numeric_budget <= 2000:
            max_ram_price = 90
        elif numeric_budget <= 3000:
            max_ram_price = 150
        else:
            max_ram_price = float('inf')
        
        ram_sizes = [64, 32, 16]
        ram_type_kw = "DDR5" if prefer_ddr5 else "DDR4"
        ram_candidates = []
        for size in ram_sizes:
            rams = RAM.objects.filter(type__icontains=ram_type_kw, size=size)
            filtered = compatibility_filter(rams, "ram", PCBuild(motherboard=chosen_mobo))
            filtered = [r for r in filtered if get_min_price(r) <= max_ram_price]
            ram_candidates += sorted(filtered, key=get_min_price, reverse=True)
        if not ram_candidates:
            logger.warning("- NOT FOUND - RAM. Skipping synergy.")
            continue
        chosen_ram = ram_candidates[0]

        # (Step 3d): Storage with set preferences per budget
        if numeric_budget <= 1000:
            max_storage_price = 80
        elif numeric_budget <= 2000:
            max_storage_price = 120
        elif numeric_budget <= 3000:
            max_storage_price = 200
        else:
            max_storage_price = float('inf')

        storage_sizes = [1000, 500]
        storage_types = ["NVME", "SATA"]
        storage_candidates = []
        for size in storage_sizes:
            for stype in storage_types:
                options = Storage.objects.filter(space__gte=size, type__icontains=stype)
                filtered = [s for s in options if get_min_price(s) <= max_storage_price]
                storage_candidates += sorted(filtered, key=get_min_price, reverse=True)
        if not storage_candidates:
            logger.warning("- NOT FOUND - Storage. Skipping synergy.")
            continue
        chosen_storage = storage_candidates[0]

        # (Step 3e): PSU, with logic for greater headroom for higher resolution systems
        partial_build = PCBuild(
            cpu=chosen_cpu, gpu=chosen_gpu, motherboard=chosen_mobo,
            ram=chosen_ram, storage=chosen_storage
        )
        resolution_is_high = resolution.lower() in ["1440p", "4k"]
        headroom = 1.5 if resolution_is_high else 1.3
        needed_wattage = int(estimate_total_power(partial_build) * headroom)
        psus = PSU.objects.filter(power__gte=needed_wattage)
        psu_candidates = sorted(psus, key=get_min_price)
        if not psu_candidates:
            logger.warning("- NOT FOUND - PSU. Skipping synergy.")
            continue
        chosen_psu = psu_candidates[len(psu_candidates) // 2]

        # (Step 3f): Case
        partial_build.psu = chosen_psu
        case_qs = compatibility_filter(Case.objects.all(), "case", partial_build)
        case_candidates = sorted(case_qs, key=get_min_price, reverse=(numeric_budget >= 3000))
        if not case_candidates:
            logger.warning("- NOT FOUND - Case. Skipping synergy.")
            continue
        chosen_case = case_candidates[0] if numeric_budget < 3000 else case_candidates[0]

        # (Step 3g): Cooler, sorting by median priced liquid coolers
        cooler_candidates = []
        for ctype in ["liquid", "air"]:
            coolers = Cooler.objects.filter(type__iexact=ctype)
            sorted_coolers = sorted(coolers, key=get_min_price)
            if sorted_coolers:
                cooler_candidates += sorted_coolers
        if not cooler_candidates:
            logger.warning("- NOT FOUND - Cooler. Skipping synergy.")
            continue
        chosen_cooler = cooler_candidates[len(cooler_candidates) // 2]

        # (Step 3h): Budget Recovery
        components = [
            chosen_cpu, chosen_gpu, chosen_mobo, chosen_ram,
            chosen_storage, chosen_psu, chosen_case, chosen_cooler
        ]
        total_price = sum(get_min_price(c) for c in components)

        recovery_candidates = {
            "motherboard": motherboard_candidates,
            "ram": ram_candidates,
            "storage": storage_candidates,
            "psu": psu_candidates,
            "case": case_candidates,
            "cooler": cooler_candidates
        }

        if total_price > numeric_budget:
            logger.debug("- Initial Build - over budget:")
            for c in components:
                logger.debug(f"  - {type(c).__name__}: {c.name} (EUR{get_min_price(c):.2f})")
            logger.debug(f"Total: EUR{total_price:.2f} > Budget: EUR{numeric_budget}")


            final_comps, final_total, success = budget_recovery(
                components, numeric_budget, partial_build, recovery_candidates
            )

            if not success or final_total > numeric_budget:
                logger.debug(f"- Budget Recovery - failed / still over budget (final: EUR {final_total:.2f}). Trying next synergy combo.")
                continue
            else:
                components = final_comps
                total_price = final_total
                logger.info(f"- ACCEPTED - Post-recovery build at EUR{total_price:.2f}")
                logger.debug("- COMPONENTS - Post-recovery components and prices:")
                for c in components:
                    logger.debug(f"  - {type(c).__name__}: {c.name} (€{get_min_price(c):.2f})")
        else:
            logger.info(f"- ACCEPTED - Initial build accepted at EUR{total_price:.2f} (within budget).")

        logger.info(f"- SUCCESS - Synergy CPU ={chosen_cpu.name}, GPU ={chosen_gpu.name}, Total = EUR{total_price:.2f}")
        new_build = PCBuild.objects.create(
            id=generate_short_id(),
            name="Smart Build",
            cpu=components[0],
            gpu=components[1],
            motherboard=components[2],
            ram=components[3],
            storage=components[4],
            psu=components[5],
            case=components[6],
            cooler=components[7]
        )
        request.session["current_build"] = str(new_build.id)
        logger.info(f"- BUILD ID - {new_build.id} created successfully.")
        return redirect(new_build.get_absolute_url())

    return HttpResponse("No valid build could be found within budget.", status=404)
