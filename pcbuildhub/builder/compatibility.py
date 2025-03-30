case_compatibility = {
    "ATX": ["ATX", "MicroATX", "ITX"],
    "MicroATX": ["MicroATX", "ITX"],
    "ITX": ["ITX"],
}

motherboard_compatibility = {
    "ATX": ["ATX"],
    "MicroATX": ["ATX", "MicroATX"],
    "ITX": ["ATX", "MicroATX", "ITX"],
}

psu_compatibility = {
    "ATX": ["ATX", "SFX"],    
    "MicroATX": ["ATX", "SFX"],  
    "ITX": ["SFX"]               
}

def estimate_total_power(build):
    total_power = 0

    if build.cpu and build.cpu.tdp:
        total_power += build.cpu.tdp
    if build.gpu and build.gpu.tdp:
        total_power += build.gpu.tdp
    if build.motherboard:
        total_power += 80  
    if build.ram:
        total_power += 30
    if build.storage:
        storage_type = build.storage.type.lower()
        if 'NVME' in storage_type:
            total_power += 10
        elif 'SATA' in storage_type:
            total_power += 15
        elif 'HDD' in storage_type:
            total_power += 20
    if build.cooler:
        cooler_type = build.cooler.type.lower()
        if 'liquid' in cooler_type:
            total_power += 15
        elif 'air' in cooler_type:
            total_power += 10

    return total_power
