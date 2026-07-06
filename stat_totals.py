"""Compute cumulated build stats for the details / comparison view.

Pure Python — no Qt dependency. Uses settings.ITEMS_DATA which must be
loaded via wakutils.setupJson() before calling.

Handles the tricky "X mastery in N elements" (and same for res) with the
following rules — given `U` user-chosen elements and item bonus `X` in
`N` elements:

  - N >= 4              → all 4 elements get +X (Case A).
  - U <= N < 4          → all U chosen get +X, plus (N-U) non-chosen (in
                          canonical order fire→water→air→earth) get +X.
  - N < U               → round-robin: N cycles of the counter, each
                          landing on the next chosen element in canonical
                          order. Deterministic across the build.
"""

from typing import Iterable

import settings
from settings import simpleActionEnum as SA
from settings import paramsActionEnum as PA
from solver import safeget, getEquipEffectValue
from stat_profile_manager import resistance_percent_to_raw


ELEM_ORDER = ("fire", "water", "air", "earth")

_ELEM_MASTERY_ACTIONS = {
    "fire":  (SA.FIRE_MASTERY_ADD,  SA.FIRE_MASTERY_MINUS),
    "water": (SA.WATER_MASTERY_ADD, SA.WATER_MASTERY_MINUS),
    "air":   (SA.AIR_MASTERY_ADD,   SA.AIR_MASTERY_MINUS),
    "earth": (SA.EARTH_MASTERY_ADD, SA.EARTH_MASTERY_MINUS),
}

_ELEM_RES_ACTIONS = {
    "fire":  (SA.FIRE_RES_ADD,  SA.FIRE_RES_MINUS),
    "water": (SA.WATER_RES_ADD, SA.WATER_RES_MINUS),
    "air":   (SA.AIR_RES_ADD,   SA.AIR_RES_MINUS),
    "earth": (SA.EARTH_RES_ADD, SA.EARTH_RES_MINUS),
}

_NON_ELEM_MASTERY_ACTIONS = {
    "crit":     (SA.CRIT_MASTERY_ADD,     SA.CRIT_MASTERY_MINUS),
    "melee":    (SA.MELEE_MASTERY_ADD,    SA.MELEE_MASTERY_MINUS),
    "back":     (SA.BACK_MASTERY_ADD,     SA.BACK_MASTERY_MINUS),
    "distance": (SA.DISTANCE_MASTERY_ADD, SA.DISTANCE_MASTERY_MINUS),
    "berzerk":  (SA.BERSERK_MASTERY_ADD,  SA.BERSERK_MASTERY_MINUS),
    "heal":     (SA.HEAL_MASTERY_ADD,     SA.HEAL_MASTERY_MINUS),
}

_NON_ELEM_PROFILE_KEY = {
    "crit":     "maitriseCritique",
    "melee":    "maitriseMelee",
    "back":     "maitriseDos",
    "distance": "maitriseDistance",
    "berzerk":  "maitriseBerserk",
    "heal":     "maitriseSoin",
}

_ATTRIBUTE_ACTIONS = {
    "PV":           (SA.PV_ADD,     SA.PV_MINUS),
    "PA":           (SA.PA_ADD,     SA.PA_MINUS),
    "PM":           (SA.PM_ADD,     SA.PM_MINUS),
    "PW":           (SA.PW_ADD,     SA.PW_MINUS),
    "PO":           (SA.PO_ADD,     SA.PO_MINUS),
    "controle":     (SA.PC_ADD,     SA.PC_MINUS),
    "initiative":   (SA.INI_ADD,    SA.INI_MINUS),
    "coupCritique": (SA.CC_ADD,     SA.CC_MINUS),
    "sagesse":      (SA.WIS_ADD,    SA.WIS_MINUS),
    "PP":           (SA.PP_ADD,     SA.PP_MINUS),
    "volonte":      (SA.WILL_ADD,   SA.WILL_MINUS),
    "parade":       (SA.BLOCK_ADD,  SA.BLOCK_MINUS),
    "tacle":        (SA.LOCK_ADD,   SA.LOCK_MINUS),
    "esquive":      (SA.DODGE_ADD,  SA.DODGE_MINUS),
}


def _sum_action(items, add_action, minus_action=None):
    """Sum ADD across items, subtract MINUS if defined (>=0)."""
    total = 0
    for item in items:
        total += getEquipEffectValue(item, add_action.value)
        if minus_action is not None and minus_action.value >= 0:
            total -= getEquipEffectValue(item, minus_action.value)
    return total


def _distribute_variable_bonus(value, N, chosen_elements, rr_counter):
    """Given one item bonus of `value` in `N` elements, return the per-
    element contribution dict. Round-robin counter is mutated in place
    (list wrapper so it acts as a mutable box)."""
    N = int(N)
    U = len(chosen_elements)

    if N >= 4:
        return {e: value for e in ELEM_ORDER}

    if U == 0:
        # No chosen elements: fall back to spreading over all 4.
        return {e: value for e in ELEM_ORDER}

    if N >= U:
        # Case B: all chosen + (N-U) non-chosen (canonical order).
        result = {e: value for e in chosen_elements}
        non_chosen = [e for e in ELEM_ORDER if e not in chosen_elements]
        for e in non_chosen[: N - U]:
            result[e] = value
        return result

    # Case C: round-robin over chosen (canonical order).
    chosen_list = [e for e in ELEM_ORDER if e in chosen_elements]
    result = {}
    for _ in range(N):
        elem = chosen_list[rr_counter[0] % U]
        result[elem] = result.get(elem, 0) + value
        rr_counter[0] += 1
    return result


def _sum_variable_bonuses(items, chosen_elements, params_action):
    """Aggregate 'X in N elements' variable bonuses over the build."""
    per_elem = {e: 0 for e in ELEM_ORDER}
    rr_counter = [0]
    for item in items:
        params = safeget(item, "definition", "equipEffects", params_action.value,
                         "effect", "definition", "params")
        if not params:
            continue
        X = params[0]
        N = params[2] if len(params) > 2 else 0
        if X == 0 or N == 0:
            continue
        contribution = _distribute_variable_bonus(X, N, chosen_elements, rr_counter)
        for e, v in contribution.items():
            per_elem[e] += v
    return per_elem


def _raw_to_pct(raw):
    """Wakfu resistance formula: pct = 1 - 0.8^(raw/100)."""
    if raw <= 0:
        return 0.0
    return round((1 - 0.8 ** (raw / 100)) * 100, 1)


def compute_totals(
    item_ids,
    base_profile_stats=None,
    chosen_elements=None,
    added_masteries=None,
):
    """Return the cumulated stats for a build.

    Parameters
    ----------
    item_ids : Iterable[int]
        Item IDs (typically from OPTIMIZED_ITEM_LIST or a saved build).
    base_profile_stats : dict or None
        Character base stats matching stat_profile_manager.DEFAULT_STATS
        keys. Values added on top of equipment. Missing keys treated as 0.
    chosen_elements : Iterable[str] or None
        Subset of ELEM_ORDER. Drives the variable-N bonus distribution.
    added_masteries : Iterable[str] or None
        Subset of {"crit", "melee", "back", "distance", "berzerk", "heal"}.
        These are added into `cumulated_mastery.total` on top of the max
        elemental mastery.
    """
    items = [settings.ITEMS_DATA[i] for i in item_ids if i in settings.ITEMS_DATA]
    profile = base_profile_stats or {}
    chosen = set(chosen_elements or [])
    added = set(added_masteries or [])

    # ─── Per-element mastery: fixed + all-elem + variable ───
    all_elem_bonus = _sum_action(items, SA.ELEM_MASTERY_ADD, SA.ELEM_MASTERY_MINUS)
    variable_mastery = _sum_variable_bonuses(items, chosen, PA.RANDOM_NUMBER_MASTERY_ADD)
    base_maitrise_elem = profile.get("maitriseElem", 0)

    elem_mastery = {}
    for elem, (add_a, minus_a) in _ELEM_MASTERY_ACTIONS.items():
        elem_mastery[elem] = (
            _sum_action(items, add_a, minus_a)
            + all_elem_bonus
            + variable_mastery[elem]
            + base_maitrise_elem
        )

    # ─── Per-element resistance (raw), then converted to % ───
    all_res_bonus = _sum_action(items, SA.ELEM_RES_ADD, SA.ELEM_RES_MINUS_UNCAPED)
    variable_res = _sum_variable_bonuses(items, chosen, PA.RANDOM_NUMBER_RES_ADD)
    base_res_raw = resistance_percent_to_raw(profile.get("resistance", 0))

    elem_res_raw = {}
    for elem, (add_a, minus_a) in _ELEM_RES_ACTIONS.items():
        elem_res_raw[elem] = (
            _sum_action(items, add_a, minus_a)
            + all_res_bonus
            + variable_res[elem]
            + base_res_raw
        )
    elem_res_pct = {e: _raw_to_pct(raw) for e, raw in elem_res_raw.items()}

    # ─── Non-elemental masteries (equipment + profile base) ───
    non_elem_mastery = {}
    for name, (add_a, minus_a) in _NON_ELEM_MASTERY_ACTIONS.items():
        v = _sum_action(items, add_a, minus_a)
        profile_key = _NON_ELEM_PROFILE_KEY.get(name)
        if profile_key:
            v += profile.get(profile_key, 0)
        non_elem_mastery[name] = v

    # ─── Attributes (PV/PA/PM/...) ───
    attributes = {}
    for stat_name, (add_a, minus_a) in _ATTRIBUTE_ACTIONS.items():
        v = _sum_action(items, add_a, minus_a)
        v += profile.get(stat_name, 0)
        attributes[stat_name] = v

    # ─── Cumulated: max elem + added masteries ───
    top_elem = max(elem_mastery, key=elem_mastery.get) if elem_mastery else "fire"
    top_value = elem_mastery.get(top_elem, 0)
    added_contributions = {name: non_elem_mastery.get(name, 0) for name in added}
    cumulated_total = top_value + sum(added_contributions.values())

    return {
        "elem_mastery":     elem_mastery,
        "elem_res_raw":     elem_res_raw,
        "elem_res_pct":     elem_res_pct,
        "non_elem_mastery": non_elem_mastery,
        "attributes":       attributes,
        "cumulated_mastery": {
            "top_elem":  top_elem,
            "top_value": top_value,
            "added":     added_contributions,
            "total":     cumulated_total,
        },
    }
