from builder.models import Motherboard, RAM, Storage, PSU, Case, Cooler, PCBuild
from .logging_config import logger
from builder.compatibility import estimate_total_power
from .helpers import get_min_price, compatibility_filter


# Function to downgrade each component in cycles, 1 step at a time, until the build fits the budget.
def budget_recovery(build_components, numeric_budget, partial_build, candidates, use_case="gaming", resolution_is_high=False, synergy_combos=None):
    
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

    for synergy_idx, (chosen_cpu, chosen_gpu, synergy_val) in enumerate(synergy_combos):
        logger.info(f"\nTrying Synergy Combo {synergy_idx + 1}: {chosen_cpu.name} + {chosen_gpu.name} (Synergy={synergy_val:.3f})")

        try:
            comps, partial_build, candidates, resolution_is_high = build_components(chosen_cpu, chosen_gpu)

            if not comps:
                logger.warning(f"[Budget Recovery] Skipped Combo {synergy_idx + 1} (CPU={chosen_cpu.name}, GPU={chosen_gpu.name}) — components returned empty list.")
                continue
            if any(c is None for c in comps):
                logger.error(f"[Budget Recovery] Skipped Combo {synergy_idx + 1} (CPU={chosen_cpu.name}, GPU={chosen_gpu.name}) — one or more components is None: {comps}")
                continue
            if len(comps) != 8:
                logger.error(f"[Budget Recovery] Skipped Combo {synergy_idx + 1} — component list size invalid: {len(comps)}")
                continue

        except Exception as e:
            logger.exception(f"[Budget Recovery] Exception for combo {synergy_idx + 1} (CPU={chosen_cpu.name}, GPU={chosen_gpu.name}) -> {e}")
            continue

        downgrade_state = {key: 0 for key in candidates.keys()}
        phases = 0
        max_total_attempts = 50

        while total_price(comps) > numeric_budget and phases < max_total_attempts:
            logger.info(f"\n\n - Budget Recovery Phase {phases + 1} (Combo {synergy_idx + 1}) -")
            partial = partial_obj(comps)

            for comp_type in ["cooler", "case", "psu", "storage", "ram", "motherboard"]:
                comp_list = candidates.get(comp_type, [])
                current_index = downgrade_state[comp_type]

                if comp_type == "ram":
                    comps, changed = downgrade_ram(comps, current_index, comp_list)
                elif comp_type == "storage":
                    comps, changed = downgrade_storage(comps, current_index, comp_list)
                elif comp_type == "psu":
                    comps, changed = downgrade_psu(comps, current_index, comp_list, partial, resolution_is_high, use_case)
                elif comp_type == "cooler":
                    comps, changed = downgrade_cooler(comps, current_index, comp_list, use_case)
                elif comp_type == "case":
                    comps, changed = downgrade_case(comps, current_index, comp_list, partial)
                elif comp_type == "motherboard":
                    comps, changed = downgrade_motherboard(comps, current_index, comp_list, partial)
                else:
                    changed = False

                if changed:
                    downgrade_state[comp_type] += 1

            phases += 1

            if total_price(comps) <= numeric_budget:
                final_price = total_price(comps)
                logger.info(f"- BUILD RECOVERED - under budget: EUR{final_price:.2f}")
                return comps, final_price, True

    logger.warning("- EXHAUSTED - Tried all synergy combos with downgrade attempts. No valid build found.")
    return None, None, False

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
    logger.info(f"- Motherboard downgraded - to {candidate.name} ({candidate.ram_type}) (EUR{get_min_price(candidate):.2f}) - Level {level}")
    return comps, True

# Function to downgrade RAM from 64 - 32 - 16GB. Candidates sorted by price descending.
def downgrade_ram(comps, level, ram_candidates):
    ram_idx = next((i for i, c in enumerate(comps) if isinstance(c, RAM)), None)
    if ram_idx is None or level >= len(ram_candidates):
        return comps, False

    new_ram = ram_candidates[level]
    comps[ram_idx] = new_ram
    logger.info(f"- RAM downgraded - to {new_ram.name} ({new_ram.size} GB) (EUR{get_min_price(new_ram):.2f}) - Level {level}")
    return comps, True

# Function to downgrade storage from NVME 1tb to SATA 1tb to NVME 500gb to SATA 500gb to then HDD.
def downgrade_storage(comps, level, storage_candidates):
    storage_idx = next((i for i, c in enumerate(comps) if isinstance(c, Storage)), None)
    if storage_idx is None or level >= len(storage_candidates):
        return comps, False

    new_storage = storage_candidates[level]
    comps[storage_idx] = new_storage
    logger.info(f"- Storage downgraded - to {new_storage.name} ({new_storage.space} GB, {new_storage.type}) (EUR{get_min_price(new_storage):.2f}) - Level {level}")
    return comps, True

# Function to downgrade PSU by reducing headroom per use case, then by cheaper price.
def downgrade_psu(comps, level, psu_candidates, partial_build, resolution_is_high, use_case="gaming"):
    psu_idx = next((i for i, c in enumerate(comps) if isinstance(c, PSU)), None)
    if psu_idx is None:
        return comps, False

    current_psu = comps[psu_idx]
    if use_case == ["editing", "dev"]:
        headroom_levels = [1.3, 1.15]
    else:
        headroom_levels = [1.5, 1.25] if resolution_is_high else [1.3, 1.15]

    if level < len(headroom_levels):
        required_power = int(estimate_total_power(partial_build) * headroom_levels[level])
        viable = [p for p in psu_candidates if p.power >= required_power]
        if viable:
            new_psu = viable[len(viable) // 2]
            if new_psu != current_psu:
                comps[psu_idx] = new_psu
                logger.info(f"- PSU downgraded - to {new_psu.name} ({new_psu.power}W) (EUR{get_min_price(new_psu):.2f}) using {int(headroom_levels[level]*100)}% headroom - Level {level}")
                return comps, True
        return comps, False

    list_index = level - len(headroom_levels)
    if list_index < len(psu_candidates):
        new_psu = psu_candidates[list_index]
        if new_psu != current_psu:
            comps[psu_idx] = new_psu
            logger.info(f"- PSU downgraded - to cheaper option: {new_psu.name} ({new_psu.power}W) (EUR{get_min_price(new_psu):.2f}) - Level {level}")
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
    logger.info(f"- Case downgraded - to {candidate.name} (EUR{get_min_price(candidate):.2f}) - Level {level}")
    return comps, True

# Function to downgrade coolers by cheaper price, then switching from liquid to air if necessary.
def downgrade_cooler(comps, level, cooler_candidates, use_case="gaming"):
    cooler_idx = next((i for i, c in enumerate(comps) if isinstance(c, Cooler)), None)
    if cooler_idx is None:
        return comps, False

    while level < len(cooler_candidates):
        candidate = cooler_candidates[level]
        current_cooler = comps[cooler_idx]
        if candidate != current_cooler:
            comps[cooler_idx] = candidate
            logger.info(f"- Cooler downgraded - to {candidate.name} ({candidate.type}) (EUR{get_min_price(candidate):.2f}) - Level {level}")
            return comps, True
        level += 1

    return comps, False