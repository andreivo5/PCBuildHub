from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from builder.models import CPU, GPU
from .recommender.predict import predict_cpu_gpu_synergy
from .utils import map_label, get_min_price, finish_smart_builder_flow, select_cpu_for_casual, select_gpu_for_casual, price_ok
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
                {"label": "€2000+", "value": "999999"},
            ],
            "dev": [
                {"label": "<€1000", "value": "1000"},
                {"label": "€1000–€2000", "value": "2000"},
                {"label": "€2000+", "value": "999999"},
            ],
            "casual": [
                {"label": "<€1000", "value": "1000"},
                {"label": "€1000–€2000", "value": "2000"},
                {"label": "€2000+", "value": "999999"},
            ]
        }
    })

def smart_builder_submit(request):
    if request.method != "POST":
        return redirect("smart_builder_home")

    use_case = request.POST.get("use_case", "gaming").lower()
    resolution = request.POST.get("resolution", "1080p")
    framerate = request.POST.get("framerate", "60")
    numeric_budget = int(request.POST.get("budget", 2000))
    casual_inputs = {
        "use": request.POST.get("casual_use", "").lower(),
        "tabs": request.POST.get("casual_tabs", "").lower(),
        "storage": request.POST.get("casual_storage", "").lower(),
        "size_pref": request.POST.get("casual_size_pref", "").lower()
    }

    if use_case == "casual":
        logger.info(f"SmartBuilder: UseCase={use_case}, Budget={numeric_budget}, Inputs={casual_inputs}")
        chosen_cpu = select_cpu_for_casual(casual_inputs, numeric_budget)
        chosen_gpu = select_gpu_for_casual(casual_inputs, chosen_cpu)

        if not chosen_cpu:
            logger.warning("Casual builder: No valid CPU found.")
            return HttpResponse("No valid CPU found for casual build.", status=404)

    else:
        synergy_label = map_label(
            use_case=use_case,
            resolution=resolution,
            framerate=framerate,
            software=request.POST.get("editing_software", ""),
            dev_type=request.POST.get("dev_type", "")
        )
        logger.info(f"SmartBuilder: UseCase={use_case}, Resolution={resolution}, FPS={framerate}, Label={synergy_label}, Budget={numeric_budget}")

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
                gpu_price = get_min_price(gpu)
                cpu_price = get_min_price(cpu)
                if gpu_price + cpu_price > numeric_budget * 0.7:
                    logger.debug(f"- Rejected - CPU + GPU combo due to price: CPU={cpu.name} (EUR {cpu_price:.2f}), GPU={gpu.name} (EUR {gpu_price:.2f})")
                    continue
                if not price_ok(cpu) or not price_ok(gpu):
                    continue

                synergy_score = predict_cpu_gpu_synergy(synergy_label, cpu, gpu, use_case)
                logger.debug(f"- Synergy Check - CPU={cpu.name}, GPU={gpu.name}, Score={synergy_score:.3f}")
                if synergy_score >= synergy_threshold:
                    combos.append((cpu, gpu, synergy_score))

        if not combos:
            logger.warning("No CPU/GPU synergy combos found by model.")
            return HttpResponse("No synergy combos found for these requirements.", status=404)

        combos.sort(key=lambda x: x[2], reverse=True)
        logger.info(f"- Found: {len(combos)} synergy combos. Trying them in descending synergy order.")

        for (candidate_cpu, candidate_gpu_repr, synergy_val) in combos:
            logger.debug(
                f"- Trying Synergy - CPU ={candidate_cpu.name} (EUR{get_min_price(candidate_cpu):.2f}), "
                f"- GPU ={candidate_gpu_repr.name} (EUR{get_min_price(candidate_gpu_repr):.2f}), "
                f"- Synergy ={synergy_val:.3f}"
            )

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

            result = finish_smart_builder_flow(request, chosen_cpu, chosen_gpu, numeric_budget, use_case, resolution, casual_inputs)
            if isinstance(result, HttpResponseRedirect):
                return result

        return HttpResponse("No valid build could be found within budget.", status=404)

    return finish_smart_builder_flow(request, chosen_cpu, chosen_gpu, numeric_budget, use_case, resolution, casual_inputs)