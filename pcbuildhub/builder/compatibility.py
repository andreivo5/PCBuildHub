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