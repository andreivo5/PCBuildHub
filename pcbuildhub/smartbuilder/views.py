from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from components.models import CPU, GPU, Motherboard, RAM, Cooler, PSU, Storage, Case
from builder.models import PCBuild
from .recommender.predict import predict_cpu_gpu_synergy
from .utils import map_label, get_min_price, generate_short_id, build_components_from_synergy
from .helpers import get_min_price
from .logging_config import logger
from .recovery import budget_recovery

def smart_builder_home(request):
    return render(request, 'smartbuild.html', {
        'use_cases': ["Gaming", "Video Editing", "Development"],
        'gaming_resolutions': ["1080p", "1440p", "4K"],
        'gaming_framerates': ["60", "120–144", "144+"],
        'editing_resolutions': ["1080p", "4K"],
        'editing_software': ["Premiere Pro", "DaVinci Resolve", "Other"],
        'dev_types': ["Web", "Mobile", "Game", "Data Science"],
        'budgets_by_use_case': {
            "gaming": [
                {"label": "<€1000", "value": "1000"},
                {"label": "€1000–€2000", "value": "2000"},
                {"label": "€2000–€3000", "value": "3000"},
                {"label": "€3000–€5000", "value": "5000"},
                {"label": "€5000+", "value": "999999"},
            ],
            "editing": [
                {"label": "<€1000", "value": "1000"},
                {"label": "€1000–€2000", "value": "2000"},
                {"label": "€2000+", "value": "4000"},
            ],
            "dev": [
                {"label": "<€1000", "value": "1000"},
                {"label": "€1000–€2000", "value": "2000"},
                {"label": "€2000+", "value": "4000"},
            ],
        }
    })

def smart_builder_submit(request):
    if request.method != "POST":
        return redirect("smart_builder_home")

    use_case = request.POST.get("use_case", "gaming").lower()
    resolution = request.POST.get("resolution", "1080p")
    framerate = request.POST.get("framerate", "60")
    numeric_budget = int(request.POST.get("budget", 2000))
    synergy_label = map_label(
        use_case=use_case,
        resolution=resolution,
        framerate=framerate,
        software=request.POST.get("editing_software", ""),
        dev_type=request.POST.get("dev_type", "")
    )

    logger.info(f"SmartBuilder: UseCase={use_case}, Resolution={resolution}, FPS={framerate}, Label={synergy_label}, Budget={numeric_budget}")

    # (Step 1): GPU & CPU gathering, sorted by performance, deduplicating GPUs by model (lowest price)
    raw_gpus = GPU.objects.exclude(g3d_mark__isnull=True).order_by("-g3d_mark")
    gpu_models = {}

    for g in raw_gpus:
        price = get_min_price(g)
        if not g.model or price < 30:
            continue
        current = gpu_models.get(g.model)
        if not current or price < get_min_price(current):
            gpu_models[g.model] = g

    unique_gpus = sorted(gpu_models.values(), key=lambda g: g.g3d_mark or 0, reverse=True)
    raw_cpus = list(CPU.objects.exclude(cpu_mark__isnull=True).order_by("-cpu_mark"))

    # (Step 2): Evaluate synergy for each CPU+GPU pair, stopping at max 100 combos with synergy 1.0
    synergy_threshold = 0.999
    combos = []
    max_combos = 30
    early_exit = False

    for gpu in unique_gpus:
        for cpu in raw_cpus:
            gpu_price = get_min_price(gpu)
            cpu_price = get_min_price(cpu)
            if gpu_price + cpu_price > numeric_budget * 0.7:
                logger.debug(f"- Rejected - CPU + GPU combo due to price: CPU={cpu.name} (EUR {cpu_price:.2f}), GPU={gpu.name} (EUR {gpu_price:.2f})")
                continue

            synergy_score = predict_cpu_gpu_synergy(synergy_label, cpu, gpu, use_case)
            score_str = f"{synergy_score:.3f}" if isinstance(synergy_score, (int, float)) else str(synergy_score)
            logger.debug(f"- Synergy Check - CPU={cpu.name}, GPU={gpu.name}, Score={score_str}")
                         
            if synergy_score >= synergy_threshold:
                combos.append((cpu, gpu, synergy_score))
                if len(combos) >= max_combos:
                    logger.info(f"Reached maximum of {max_combos} synergy matches. Skipping further evaluation.")
                    early_exit = True
                    break
        if early_exit:
            break

    if not combos:
        logger.warning("No CPU/GPU synergy combos found by model.")
        return JsonResponse({"error": "No valid build could be found within budget."}, status=404)

    combos.sort(key=lambda x: get_min_price(x[0]) + get_min_price(x[1]), reverse=True)
    logger.info(f"- Found: {len(combos)} synergy combos. Trying them in descending price order.")

    first_cpu, first_gpu, _ = combos[0]
    try:
        components, partial_build, recovery_candidates, resolution_is_high = build_components_from_synergy(
            first_cpu, first_gpu, synergy_label, numeric_budget, use_case, resolution
        )
    except Exception as e:
        logger.exception(f"[Smart Builder] Exception during initial build for Synergy Combo 0 (CPU={first_cpu.name}, GPU={first_gpu.name}) -> {e}")
        components = None

    if components is None:
        logger.warning(f"[Smart Builder] Initial build failed for Synergy Combo 0 (CPU={first_cpu.name}, GPU={first_gpu.name}) — missing components.")
        components, total_price, success = budget_recovery(
            lambda cpu, gpu: build_components_from_synergy(cpu, gpu, synergy_label, numeric_budget, use_case, resolution),
            numeric_budget,
            None,
            None,
            use_case,
            False,
            synergy_combos=combos
        )
    else:
        total_price = sum(get_min_price(c) for c in components)
        if total_price > numeric_budget:
            logger.debug("- Initial Build - over budget:")
            for c in components:
                logger.debug(f"  - {type(c).__name__}: {c.name} (EUR{get_min_price(c):.2f})")
            components, total_price, success = budget_recovery(
                lambda cpu, gpu: build_components_from_synergy(cpu, gpu, synergy_label, numeric_budget, use_case, resolution),
                numeric_budget,
                partial_build,
                recovery_candidates,
                use_case,
                resolution_is_high,
                synergy_combos=combos
            )
        else:
            success = True

    if success:
        logger.info(f"- SUCCESS - Final build total: EUR{total_price:.2f}")
        for c in components:
            logger.debug(f"  - {type(c).__name__}: {c.name} (EUR{get_min_price(c):.2f})")
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

        if request.user.is_authenticated:
            new_build.owner = request.user
            new_build.save()
        else:
            guest = request.session.get("guest_builds", [])
            if new_build.id not in guest:
                guest.append(new_build.id)
                request.session["guest_builds"] = guest
        request.session["current_build"] = str(new_build.id)
        logger.info(f"- BUILD ID - {new_build.id} created successfully.")
        return redirect(new_build.get_absolute_url())

    return JsonResponse({"error": "No valid build could be found within budget."}, status=404)
