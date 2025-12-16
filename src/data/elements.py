ELEMENT_CHART = {
    "Fire":     {"strong": ["Grass"], "weak": ["Water"]},
    "Water":    {"strong": ["Fire"], "weak": ["Grass"]},
    "Grass":    {"strong": ["Water"], "weak": ["Fire"]},
    "Electric": {"strong": ["Land"], "weak": []},
    "Normal":   {"strong": [], "weak": []},
    "Ice": {"strong": ["Water"], "weak": ["Fire"]},
    "Land": {"strong": ["Grass"], "weak": ["Electric"]},
}

def compute_element_multiplier(attacker_element: str, defender_element: str) -> float:
    if defender_element in ELEMENT_CHART[attacker_element]["strong"]:
        return 1.5
    if defender_element in ELEMENT_CHART[attacker_element]["weak"]:
        return 0.5
    return 1.0
