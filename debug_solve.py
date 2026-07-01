"""Headless solver runner for debugging.

Usage:
    python3 debug_solve.py [--level N] [--elements W,A,...] [--force ID,ID,...]
                           [--forbid ID,ID,...]

Runs the same solver as the UI, prints the chosen items and the total stats.
"""

import argparse
import sys

from PySide6.QtCore import QCoreApplication

import settings
from wakutils import setupJson, slot_of, name_of
from solver import getEquipEffectValue, getEquipEffectValueWithParams


def _get_constraint(model, name):
    for c in model.getConstraints():
        if c.getName() == name:
            return c
    raise KeyError(f"unknown constraint: {name}")


def _set_rarity(selector, enabled_rarities):
    """Enable/disable rarity toggles by their display color."""
    # Constraint names → color used by rarityEnum
    mapping = {
        "rarityCommonSelector":    "white",
        "rarityRareSelector":      "green",
        "rarityMythicalSelector":  "orange",
        "rarityLegendarySelector": "yellow",
        "rarityMemorySelector":    "lightblue",
        "rarityEpicSelector":      "purple",
        "rarityRelicSelector":     "pink",
    }
    for name, color in mapping.items():
        _get_constraint(selector.simpleConstraintModel, name).setValue(
            1 if color in enabled_rarities else 0
        )


def _set_elements(selector, elements):
    """Enable the elemental masteries to maximize (subset of fire/water/air/earth)."""
    mapping = {
        "fire":  "fireSelector",
        "water": "waterSelector",
        "air":   "airSelector",
        "earth": "earthSelector",
    }
    for elem, cname in mapping.items():
        _get_constraint(selector.maximizeElemMasteryModel, cname).setValue(
            1 if elem in elements else 0
        )


def _set_other_masteries(selector, masteries):
    """Enable non-elemental masteries to maximize (crit / back / melee / heal / distance / berzerk)."""
    mapping = {
        "crit":     "critMasterySelector",
        "back":     "backMasterySelector",
        "melee":    "meleeMasterySelector",
        "heal":     "healMasterySelector",
        "distance": "distanceMasterySelector",
        "berzerk":  "berzerkMasterySelector",
    }
    for name, cname in mapping.items():
        _get_constraint(selector.maximizeOtherMasteryModel, cname).setValue(
            1 if name in masteries else 0
        )


def _compute_stats(item_ids):
    """Return {'stat_name': int_value} for the given item ids, matching WakfuItemStatSum."""
    from settings import simpleActionEnum, paramsActionEnum

    rows = []
    for data in simpleActionEnum:
        val = 0
        for iid in item_ids:
            val += getEquipEffectValue(settings.ITEMS_DATA[iid], data.value)
        if val != 0:
            desc = settings.ACTION_DATA[data.value]["definition"]["effect"]
            rows.append((desc, val, None))

    for data in paramsActionEnum:
        val = 0
        nb = 0
        for iid in item_ids:
            temp = getEquipEffectValueWithParams(settings.ITEMS_DATA[iid], data.value)
            val += temp
            if temp != 0:
                nb = settings.ITEMS_DATA[iid]["definition"]["equipEffects"][data.value]["effect"]["definition"]["params"][2]
        if val != 0:
            desc = settings.ACTION_DATA[data.value]["definition"]["effect"]
            rows.append((desc, val, nb))
    return rows


def _solve_with_forced(sel, forced_ids):
    """Run initSolver + add V[id]==1 for each forced id + Solve, without recursing into sel.solve()."""
    from ortools.linear_solver import pywraplp

    sel._applyStatProfile()
    sel.initSolver()

    infeasible = []
    for iid in forced_ids:
        if iid not in settings.VARIABLES:
            infeasible.append(iid)
            continue
        sel.solver.Add(settings.VARIABLES[iid] == 1)

    status = sel.solver.Solve()
    settings.OPTIMIZED_ITEM_LIST = []
    if status == pywraplp.Solver.OPTIMAL:
        for key, var in settings.VARIABLES.items():
            if var.solution_value() == 1:
                settings.OPTIMIZED_ITEM_LIST.append(key)
    else:
        print(f"⚠  solver status = {status} (not OPTIMAL) — infeasible with these forced items")
    return infeasible


def run(*, level=230, rarities=("white", "green", "orange", "yellow",
                                "lightblue", "purple", "pink"),
        elements=("water", "air"), other_masteries=(),
        pa=0, pm=0, force=(), forbid=()):

    _app = QCoreApplication.instance() or QCoreApplication(sys.argv)
    settings.initGlobal()
    setupJson()

    from wakfuConstraintSelector import WakfuConstraintSelector
    sel = WakfuConstraintSelector()
    _get_constraint(sel.simpleConstraintModel, "levelSelector").setValue(level)
    _get_constraint(sel.simpleConstraintModel, "paSelector").setValue(pa)
    _get_constraint(sel.simpleConstraintModel, "pmSelector").setValue(pm)
    _set_rarity(sel, set(rarities))
    _set_elements(sel, set(elements))
    _set_other_masteries(sel, set(other_masteries))

    for iid in forbid:
        sel.addExcludedItem(int(iid))

    print(f"Config: level<={level}  PA>={pa}  PM>={pm}  "
          f"rarities={rarities}  elements={elements}  other={other_masteries}")
    if force:
        print(f"Forcing items: {[name_of(int(i)) for i in force]}")
    if forbid:
        print(f"Excluding items: {[name_of(int(i)) for i in forbid]}")
    print()

    forced_ids = [int(i) for i in force]
    if forced_ids:
        infeasible = _solve_with_forced(sel, forced_ids)
        if infeasible:
            print(f"⚠  IDs not in VARIABLES (filtered by level/rarity/exclude): "
                  f"{[(i, name_of(i)) for i in infeasible]}")
    else:
        sel.solve()

    picked = list(settings.OPTIMIZED_ITEM_LIST)

    print()
    print("── Items picked (in slot order) ──")
    for iid in sorted(picked, key=lambda i: (slot_of(i), i)):
        print(f"  [{slot_of(iid):<16}] {iid:>6}  {name_of(iid)}")

    print()
    print("── Total stats ──")
    for desc, val, nb in _compute_stats(picked):
        if nb is None:
            print(f"  {desc:<50} {val:>6}")
        else:
            print(f"  {desc:<50} {val:>6}  (on {int(nb)} element)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--level", type=int, default=230)
    p.add_argument("--rarities", default="white,green,orange,yellow,lightblue,purple,pink",
                   help="comma-separated colors: white,green,orange,yellow,lightblue,purple,pink")
    p.add_argument("--elements", default="water,air",
                   help="comma-separated: fire,water,air,earth")
    p.add_argument("--other-masteries", dest="other_masteries", default="",
                   help="comma-separated: crit,back,melee,heal,distance,berzerk")
    p.add_argument("--pa", type=int, default=0)
    p.add_argument("--pm", type=int, default=0)
    p.add_argument("--force", default="",
                   help="comma-separated item IDs — added to --forbid list of every OTHER "
                        "same-slot item so these get picked (rudimentary; requires manual work)")
    p.add_argument("--forbid", default="",
                   help="comma-separated item IDs to exclude from the solver")
    args = p.parse_args()

    run(
        level=args.level,
        rarities=tuple(x for x in args.rarities.split(",") if x),
        elements=tuple(x for x in args.elements.split(",") if x),
        other_masteries=tuple(x for x in args.other_masteries.split(",") if x),
        pa=args.pa,
        pm=args.pm,
        force=tuple(x for x in args.force.split(",") if x),
        forbid=tuple(x for x in args.forbid.split(",") if x),
    )


if __name__ == "__main__":
    main()
