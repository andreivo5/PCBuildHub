import random, string
from builder.compatibility import estimate_total_power
from builder.models import CPU, GPU, Motherboard, RAM, Storage, PSU, Case, Cooler, PCBuild
from .logging_config import logger
from .helpers import get_min_price, compatibility_filter

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

def build_components_from_synergy(cpu, gpu, synergy_label, numeric_budget, use_case, resolution):
    try:
        logger.debug(f"- Trying Synergy - CPU ={cpu.name} (EUR{get_min_price(cpu):.2f}), "
                    f"GPU ={gpu.name} (EUR{get_min_price(gpu):.2f})")
    except Exception as e:
        logger.exception(f"[Build Components] Exception during initial debug log for CPU={cpu.name}, GPU={gpu.name} -> {e}")
        return None, None, None, None

    # --- MOTHERBOARD ---
    prefer_ddr5 = numeric_budget > 1500 or use_case in ["editing", "dev"]
    mobos = Motherboard.objects.filter(socket=cpu.socket)
    if prefer_ddr5:
        ddr5_mobos = mobos.filter(ram_type__icontains="DDR5")
        if ddr5_mobos.exists():
            mobos = ddr5_mobos
        else:
            prefer_ddr5 = False

    sorted_mobos = sorted(mobos, key=get_min_price, reverse=True)
    seen_prices = set()
    motherboard_candidates = []
    for mobo in sorted_mobos:
        price = get_min_price(mobo)
        if price not in seen_prices:
            motherboard_candidates.append(mobo)
            seen_prices.add(price)
    if not motherboard_candidates:
        logger.warning(f"[Build Failure] No compatible motherboard found for CPU socket '{cpu.socket}' (CPU: {cpu.name})")
        return None, None, None, None
    chosen_mobo = motherboard_candidates[0]
    logger.info(f"[Motherboard] Selected: {chosen_mobo.name} (EUR{get_min_price(chosen_mobo):.2f}) — DDR5 preferred: {prefer_ddr5}, Total candidates: {len(motherboard_candidates)}")

    # --- RAM ---
    if numeric_budget <= 1000:
        max_ram_price = 200
    elif numeric_budget <= 2000:
        max_ram_price = 350
    elif numeric_budget <= 3000:
        max_ram_price = 500
    else:
        max_ram_price = float('inf')

    if use_case == "dev" and ("datasci" in synergy_label or "game" in synergy_label):
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
        seen_prices = set()
        unique_rams = []
        for r in sorted(filtered, key=get_min_price, reverse=True):
            price = get_min_price(r)
            if price not in seen_prices:
                unique_rams.append(r)
                seen_prices.add(price)
        ram_candidates += unique_rams
    if not ram_candidates:
        logger.warning(f"[Build Failure] No compatible RAM found (Type: {ram_type_kw}) for Motherboard: {chosen_mobo.name}")
        return None, None, None, None
    chosen_ram = ram_candidates[0]
    logger.info(f"[RAM] Selected: {chosen_ram.name} (EUR{get_min_price(chosen_ram):.2f}) — Type: {ram_type_kw}, Max price: EUR{max_ram_price}, Total candidates: {len(ram_candidates)}")

    # --- STORAGE ---
    if numeric_budget <= 1000:
        max_storage_price = 200
    elif numeric_budget <= 2000:
        max_storage_price = 400
    elif numeric_budget <= 3000:
        max_storage_price = 600
    else:
        max_storage_price = float('inf')

    if use_case == "editing" or (use_case == "dev" and ("datasci" in synergy_label or "game" in synergy_label)):
        storage_sizes = [2000, 1000, 500]
    else:
        storage_sizes = [1000, 500]

    storage_types = ["NVME", "SATA"]
    storage_candidates = []
    for size in storage_sizes:
        for stype in storage_types:
            options = Storage.objects.filter(space__gte=size, type__icontains=stype)
            filtered = [s for s in options if get_min_price(s) <= max_storage_price]
            seen_prices = set()
            unique_options = []
            for s in sorted(filtered, key=get_min_price, reverse=True):
                price = get_min_price(s)
                if price not in seen_prices:
                    unique_options.append(s)
                    seen_prices.add(price)
            storage_candidates += unique_options
    if not storage_candidates:
        logger.warning(f"[Build Failure] No storage options found under price cap EUR{max_storage_price:.2f}")
        return None, None, None, None
    chosen_storage = storage_candidates[0]
    logger.info(f"[Storage] Selected: {chosen_storage.name} (EUR{get_min_price(chosen_storage):.2f}) — Sizes tried: {storage_sizes}, Max price: EUR{max_storage_price}, Total candidates: {len(storage_candidates)}")

    # --- PSU ---
    partial_build = PCBuild(
        cpu=cpu, gpu=gpu, motherboard=chosen_mobo,
        ram=chosen_ram, storage=chosen_storage
    )
    resolution_is_high = resolution.lower() in ["1440p", "4k"] or use_case in ["editing", "dev"]
    headroom = 1.5 if resolution_is_high else 1.3
    needed_wattage = int(estimate_total_power(partial_build) * headroom)

    psus = PSU.objects.filter(power__gte=needed_wattage)
    psus = sorted(psus, key=get_min_price, reverse=True)
    seen_prices = set()
    unique_psus = []
    for psu in psus:
        price = get_min_price(psu)
        if price not in seen_prices:
            unique_psus.append(psu)
            seen_prices.add(price)
    if not unique_psus:
        logger.warning(f"[Build Failure] No PSU found for estimated power draw of {needed_wattage}W (Headroom: {headroom})")
        return None, None, None, None
    chosen_psu = unique_psus[0]
    partial_build.psu = chosen_psu
    logger.info(f"[PSU] Selected: {chosen_psu.name} (EUR{get_min_price(chosen_psu):.2f}) — Required wattage: {needed_wattage}W, Headroom: {headroom}, Total candidates: {len(unique_psus)}")

    # --- CASE ---
    case_qs = compatibility_filter(Case.objects.all(), "case", partial_build)
    case_qs = sorted(case_qs, key=get_min_price, reverse=True)
    unique_cases = []
    seen_prices = set()
    for case in case_qs:
        price = get_min_price(case)
        if price not in seen_prices:
            unique_cases.append(case)
            seen_prices.add(price)
    if not unique_cases:
        logger.warning(f"[Build Failure] No compatible PC case found for build (Motherboard: {chosen_mobo.name}, PSU: {chosen_psu.name})")
        return None, None, None, None
    chosen_case = unique_cases[0]
    logger.info(f"[Case] Selected: {chosen_case.name} (EUR{get_min_price(chosen_case):.2f}) — Total compatible cases: {len(unique_cases)}")

    # --- COOLER ---
    coolers = Cooler.objects.filter(type__in=["liquid", "air"])
    coolers = [c for c in coolers if get_min_price(c) >= 30]
    seen = set()
    unique_coolers = []
    for c in sorted(coolers, key=get_min_price, reverse=True):
        price = round(get_min_price(c), 2)
        if price not in seen:
            seen.add(price)
            unique_coolers.append(c)
    if not unique_coolers:
        logger.warning(f"[Build Failure] No suitable cooler found over EUR30 for build (CPU: {cpu.name})")
        return None, None, None, None
    chosen_cooler = unique_coolers[0]
    logger.info(f"[Cooler] Selected: {chosen_cooler.name} (EUR{get_min_price(chosen_cooler):.2f}) — Filtered from: {len(unique_coolers)} options")

    components = [
        cpu, gpu, chosen_mobo, chosen_ram,
        chosen_storage, chosen_psu, chosen_case, chosen_cooler
    ]

    recovery_candidates = {
        "motherboard": motherboard_candidates,
        "ram": ram_candidates,
        "storage": storage_candidates,
        "psu": unique_psus,
        "case": unique_cases,
        "cooler": unique_coolers
    }

    for comp in components:
        if comp is None:
            logger.error(f"[Build Components] Found None in components list before return. CPU={cpu.name}, GPU={gpu.name}")

    return components, partial_build, recovery_candidates, resolution_is_high
