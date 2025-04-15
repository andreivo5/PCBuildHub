from builder.models import Motherboard, RAM, Storage, PSU, Case, Cooler, PCBuild
from .logging_config import logger
from .utils import get_min_price, compatibility_filter
from builder.compatibility import estimate_total_power

# Function to downgrade each component in cycles, 1 step at a time, until the build fits the budget.
def budget_recovery(build_components, numeric_budget, partial_build, candidates):
    logger.warning("- STARTING BUDGET RECOVERY - ")

    def total_price(comps):
        return sum(get_min_price(x) for x in comps if x)

    def partial_obj(comps):
        cdict = {type(c).__name__.lower(): c for c in comps if c}
        return PCBuild(
            cpu=cdict.get('cpu'),
            gpu=cdict.get('gpu'),
            motherboard=cdict.get('motherboard'),
            ram=cdict.get('ram'),
            storage=cdict.get('storage'),
            psu=cdict.get('psu'),
            case=cdict.get('case'),
            cooler=cdict.get('cooler'),
        )

    comps = build_components[:]
    phases = 0
    max_phases = 10
    success = False
    resolution_is_high = False
    if partial_build and partial_build.gpu:
        resolution_is_high = partial_build.gpu and partial_build.gpu.resolution in ["1440p", "4k"]

    downgrade_state = {key: 0 for key in candidates.keys()}

    while total_price(comps) > numeric_budget and phases < max_phases:
        logger.info(f"\n\n - Budget Recovery Phase {phases + 1} -")
        partial = partial_obj(comps)

        for comp_type in ["cooler", "case", "psu", "storage", "ram", "motherboard"]:
            comp_list = candidates.get(comp_type, [])
            current_index = downgrade_state[comp_type]

            if comp_type == "ram":
                comps, changed = downgrade_ram(comps, current_index, comp_list)
            elif comp_type == "storage":
                comps, changed = downgrade_storage(comps, current_index, comp_list)
            elif comp_type == "psu":
                comps, changed = downgrade_psu(comps, current_index, comp_list, partial, resolution_is_high)
            elif comp_type == "cooler":
                comps, changed = downgrade_cooler(comps, current_index, comp_list)
            elif comp_type == "case":
                comps, changed = downgrade_case(comps, current_index, comp_list, partial)
            elif comp_type == "motherboard":
                comps, changed = downgrade_motherboard(comps, current_index, comp_list, partial)
            else:
                changed = False

            if changed:
                downgrade_state[comp_type] += 1

        phases += 1

    final_price = total_price(comps)
    success = final_price <= numeric_budget
    if success:
        logger.info(f"- BUILD RECOVERED - under budget: EUR{final_price:.2f}")
    else:
        logger.warning("- EXHAUSTED - Budget recovery. Trying next CPU+GPU combo.")

    return comps, final_price, success

# Function to downgrade RAM from 64 - 32 - 16GB. Candidates sorted by price descending.
def downgrade_ram(comps, level, ram_candidates):
    ram_idx = next((i for i, c in enumerate(comps) if isinstance(c, RAM)), None)
    if ram_idx is None or level >= len(ram_candidates):
        return comps, False

    new_ram = ram_candidates[level]
    comps[ram_idx] = new_ram
    logger.info(f"- RAM downgraded - to {new_ram.name} ({new_ram.size} GB) - Level {level}")
    return comps, True

# Function to downgrade storage from NVME 1tb to SATA 1tb to NVME 500gb to SATA 500gb to then HDD.
def downgrade_storage(comps, level, storage_candidates):
    storage_idx = next((i for i, c in enumerate(comps) if isinstance(c, Storage)), None)
    if storage_idx is None or level >= len(storage_candidates):
        return comps, False

    new_storage = storage_candidates[level]
    comps[storage_idx] = new_storage
    logger.info(f"- Storage downgraded - to {new_storage.name} ({new_storage.space} GB, {new_storage.type}) - Level {level}")
    return comps, True

# Function to downgrade PSU by reducing headroom from 50% to 25%, then by cheaper price.
def downgrade_psu(comps, level, psu_candidates, partial_build, resolution_is_high):
    psu_idx = next((i for i, c in enumerate(comps) if isinstance(c, PSU)), None)
    if psu_idx is None:
        return comps, False

    current_psu = comps[psu_idx]
    headroom_levels = [1.5, 1.25] if resolution_is_high else [1.3, 1.15]

    if level < len(headroom_levels):
        required_power = int(estimate_total_power(partial_build) * headroom_levels[level])
        viable = [p for p in psu_candidates if p.power >= required_power]
        if viable:
            new_psu = viable[len(viable) // 2]
            if new_psu != current_psu:
                comps[psu_idx] = new_psu
                logger.info(f"- PSU downgraded - to {new_psu.name} ({new_psu.power}W) using {int(headroom_levels[level]*100)}% headroom.")
                return comps, True
        return comps, False

    list_index = level - len(headroom_levels)
    if list_index < len(psu_candidates):
        new_psu = psu_candidates[list_index]
        if new_psu != current_psu:
            comps[psu_idx] = new_psu
            logger.info(f"- PSU downgraded - to cheaper option: {new_psu.name} ({new_psu.power}W)")
            return comps, True

    return comps, False

# Function to downgrade coolers by cheaper price, then switching from liquid to air if necessary.
def downgrade_cooler(comps, level, cooler_candidates):
    cooler_idx = next((i for i, c in enumerate(comps) if isinstance(c, Cooler)), None)
    if cooler_idx is None or level >= len(cooler_candidates):
        return comps, False

    current_cooler = comps[cooler_idx]
    candidate = cooler_candidates[level]

    if candidate != current_cooler:
        comps[cooler_idx] = candidate
        logger.info(f"- Cooler downgraded - to {candidate.name} ({candidate.type}) - Level {level}")
        return comps, True

    return comps, False

# Function to downgrade case from expensive to cheaper, maintaining compatibility.
def downgrade_case(comps, level, case_candidates, partial_build):
    case_idx = next((i for i, c in enumerate(comps) if isinstance(c, Case)), None)
    if case_idx is None or level >= len(case_candidates):
        return comps, False

    candidate = case_candidates[level]
    test_build = PCBuild(
        cpu=partial_build.cpu,
        gpu=partial_build.gpu,
        motherboard=partial_build.motherboard,
        ram=partial_build.ram,
        storage=partial_build.storage,
        psu=partial_build.psu,
        cooler=partial_build.cooler,
        case=candidate
    )

    filtered = compatibility_filter(Case.objects.filter(pk=candidate.pk), "case", test_build)
    if not filtered.exists():
        return comps, False

    comps[case_idx] = candidate
    logger.info(f"- Case downgraded - to {candidate.name} - Level {level}")
    return comps, True

# Function to downgrade motherboard from expensive to cheaper, maintaining compatibility.
def downgrade_motherboard(comps, level, mobo_candidates, partial_build):
    mobo_idx = next((i for i, c in enumerate(comps) if isinstance(c, Motherboard)), None)
    if mobo_idx is None or level >= len(mobo_candidates):
        return comps, False

    candidate = mobo_candidates[level]
    current_ram = partial_build.ram

    if current_ram and candidate.ram_type and candidate.ram_type not in current_ram.type:
        return comps, False

    comps[mobo_idx] = candidate
    logger.info(f"- Motherboard downgraded - to {candidate.name} ({candidate.ram_type}) - Level {level}")
    return comps, True