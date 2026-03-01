"""
Wakfu damage calculator — standalone utility.

Implements the damage formulas from WakfuCalc (by Ectawem):
https://sites.google.com/view/wakfucalc/fr/guides/formules

Usage:
    python damage_calculator.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum


class Element(Enum):
    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"
    AIR = "air"
    LIGHT = "light"
    STASIS = "stasis"


class Orientation(Enum):
    FRONT = "front"
    SIDE = "side"
    BACK = "back"


ORIENTATION_BONUS = {
    Orientation.FRONT: 1.0,
    Orientation.SIDE: 1.1,
    Orientation.BACK: 1.25,
}


@dataclass
class CasterStats:
    elemental_mastery: int = 0
    critical_mastery: int = 0
    melee_mastery: int = 0
    distance_mastery: int = 0
    berserk_mastery: int = 0
    back_mastery: int = 0
    heal_mastery: int = 0

    critical_chance: int = 0  # in %, clamped 0-100
    damage_inflicted: int = 0  # % DI (regular + conditional combined)

    is_berserk: bool = False  # below 50% HP


@dataclass
class TargetStats:
    elemental_resistance: int = 0  # flat resistance for the relevant element
    critical_resistance: int = 0
    back_resistance: int = 0

    parade_chance: int = 0  # % chance to block
    has_expert_block: bool = False  # sublimation Expert des Parades
    damage_received: int = 100  # % Dommages Reçus (default 100%)


@dataclass
class Spell:
    base: float = 0
    element: Element = Element.FIRE
    can_crit: bool = True
    orientation: Orientation = Orientation.FRONT

    is_melee: bool = True  # target within 1-2 cells
    is_indirect: bool = False  # poison, glyph, trap

    bonus_damage_inflicted: int = 0  # per-spell % DI bonus ("options ponctuelles")
    bonus_mastery: int = 0
    bonus_critical_mastery: int = 0
    bonus_critical_chance: int = 0
    bonus_base_percent: int = 0  # +X% on base value


# ---------------------------------------------------------------------------
# Core formulas
# ---------------------------------------------------------------------------

def flat_res_to_percent(flat_resistance: int) -> int:
    """Convert flat resistance to % resistance (floored), capped at 90%."""
    pct = (1.0 - 0.8 ** (flat_resistance / 100.0)) * 100.0
    # round to 9 decimals to neutralize float artifacts (e.g. 19.9999… → 20.0)
    pct = round(pct, 9)
    return min(int(math.floor(pct)), 90)


def percent_res_to_flat(percent_resistance: int) -> int:
    """Convert % resistance back to flat resistance (ceiled)."""
    if percent_resistance <= 0:
        return 0
    if percent_resistance >= 100:
        raise ValueError("% resistance must be < 100")
    raw = 100.0 * math.log(1.0 - percent_resistance / 100.0) / math.log(0.8)
    return int(math.ceil(raw))


def compute_applicable_masteries(
    caster: CasterStats,
    spell: Spell,
    is_crit: bool,
    orientation: Orientation,
) -> int:
    """Sum all applicable masteries for a given context."""
    total = caster.elemental_mastery + spell.bonus_mastery

    if spell.is_melee:
        total += caster.melee_mastery
    else:
        total += caster.distance_mastery

    if caster.is_berserk:
        total += caster.berserk_mastery

    if not spell.is_indirect and orientation == Orientation.BACK:
        total += caster.back_mastery

    if is_crit and spell.can_crit:
        total += caster.critical_mastery + spell.bonus_critical_mastery

    return total


def compute_effective_resistance(
    target: TargetStats,
    is_crit: bool,
    orientation: Orientation,
    is_indirect: bool,
) -> int:
    """Compute total flat resistance, then convert to %."""
    flat = target.elemental_resistance

    if is_crit:
        flat += target.critical_resistance

    if not is_indirect and orientation == Orientation.BACK:
        flat += target.back_resistance

    return flat_res_to_percent(flat)


def compute_parade_coefficient(is_parried: bool, has_expert_block: bool) -> float:
    if not is_parried:
        return 1.0
    return 0.68 if has_expert_block else 0.8


def compute_spell_damage_raw(
    caster: CasterStats,
    target: TargetStats,
    spell: Spell,
    is_crit: bool,
    is_parried: bool = False,
) -> float:
    """Compute exact (non-rounded) damage for a single spell hit."""
    orientation = Orientation.FRONT if spell.is_indirect else spell.orientation

    base = spell.base * (1 + spell.bonus_base_percent / 100.0)

    # The game rounds the crit base up before applying other multipliers
    if is_crit and spell.can_crit:
        base = math.ceil(base * 1.25)

    masteries = compute_applicable_masteries(caster, spell, is_crit, orientation)
    mastery_factor = 1.0 + masteries / 100.0

    orientation_bonus = 1.0 if spell.is_indirect else ORIENTATION_BONUS[orientation]

    total_di = caster.damage_inflicted + spell.bonus_damage_inflicted
    di_factor = 1.0 + total_di / 100.0

    res_pct = compute_effective_resistance(
        target, is_crit, orientation, spell.is_indirect
    )
    res_factor = 1.0 - res_pct / 100.0

    dr_factor = target.damage_received / 100.0

    parade_coeff = compute_parade_coefficient(is_parried, target.has_expert_block)

    return (
        base
        * mastery_factor
        * orientation_bonus
        * di_factor
        * res_factor
        * dr_factor
        * parade_coeff
    )


def compute_spell_damage(
    caster: CasterStats,
    target: TargetStats,
    spell: Spell,
    is_crit: bool,
    is_parried: bool = False,
) -> int:
    """Compute floored damage (minimum possible roll)."""
    return int(math.floor(compute_spell_damage_raw(caster, target, spell, is_crit, is_parried)))


@dataclass
class StochasticDamage:
    """Represents a damage value with stochastic rounding."""
    raw: float = 0.0
    low: int = 0       # floor
    high: int = 0      # ceil
    chance_high: float = 0.0  # probability of getting `high`

    @staticmethod
    def from_raw(raw: float) -> StochasticDamage:
        low = int(math.floor(raw))
        high = int(math.ceil(raw))
        chance_high = raw - low if high != low else 0.0
        return StochasticDamage(raw=raw, low=low, high=high, chance_high=chance_high)


@dataclass
class DamageResult:
    non_crit: StochasticDamage = field(default_factory=StochasticDamage)
    crit: StochasticDamage = field(default_factory=StochasticDamage)
    average: float = 0.0

    non_crit_parried: StochasticDamage = field(default_factory=StochasticDamage)
    crit_parried: StochasticDamage = field(default_factory=StochasticDamage)
    average_with_parade: float = 0.0


def compute_damage(
    caster: CasterStats,
    target: TargetStats,
    spell: Spell,
) -> DamageResult:
    """Compute all damage variants for a spell and return a summary."""
    cc = min(max(caster.critical_chance + spell.bonus_critical_chance, 0), 100)
    cc_ratio = cc / 100.0

    nc_raw = compute_spell_damage_raw(caster, target, spell, is_crit=False)
    cr_raw = compute_spell_damage_raw(caster, target, spell, is_crit=True) if spell.can_crit else nc_raw
    average = nc_raw * (1.0 - cc_ratio) + cr_raw * cc_ratio

    ncp_raw = compute_spell_damage_raw(caster, target, spell, is_crit=False, is_parried=True)
    crp_raw = compute_spell_damage_raw(caster, target, spell, is_crit=True, is_parried=True) if spell.can_crit else ncp_raw

    parade_pct = target.parade_chance / 100.0
    avg_nc = nc_raw * (1.0 - parade_pct) + ncp_raw * parade_pct
    avg_cr = cr_raw * (1.0 - parade_pct) + crp_raw * parade_pct
    average_with_parade = avg_nc * (1.0 - cc_ratio) + avg_cr * cc_ratio

    return DamageResult(
        non_crit=StochasticDamage.from_raw(nc_raw),
        crit=StochasticDamage.from_raw(cr_raw),
        average=average,
        non_crit_parried=StochasticDamage.from_raw(ncp_raw),
        crit_parried=StochasticDamage.from_raw(crp_raw),
        average_with_parade=average_with_parade,
    )


def compute_effective_mastery(
    caster: CasterStats,
    spell: Spell,
    include_crit: bool = False,
) -> float:
    """
    EM = ((Masteries + 100) × (% DI + 100) / 100) - 100
    EMcrit multiplies the base by 1.25 and includes crit mastery.
    """
    masteries = caster.elemental_mastery
    if spell.is_melee:
        masteries += caster.melee_mastery
    else:
        masteries += caster.distance_mastery
    if caster.is_berserk:
        masteries += caster.berserk_mastery

    di = caster.damage_inflicted

    if not include_crit:
        em = ((masteries + 100) * (di + 100) / 100.0) - 100
    else:
        masteries += caster.critical_mastery
        em = (((masteries + 100) * (di + 100) / 100.0) - 100) * 1.25

    return em


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    caster = CasterStats(
        elemental_mastery=1500,
        critical_mastery=200,
        melee_mastery=300,
        critical_chance=40,
        damage_inflicted=30,
    )
    target = TargetStats(
        elemental_resistance=400,
        parade_chance=20,
    )
    spell = Spell(base=115, element=Element.FIRE, orientation=Orientation.FRONT)

    result = compute_damage(caster, target, spell)

    def fmt(sd: StochasticDamage) -> str:
        if sd.low == sd.high:
            return f"{sd.low}"
        return f"{sd.low} or {sd.high}  (raw {sd.raw:.2f}, {sd.chance_high:.0%} chance of {sd.high})"

    print("=== Wakfu Damage Calculator ===")
    print(f"Non-crit:  {fmt(result.non_crit)}")
    print(f"Crit:      {fmt(result.crit)}")
    print(f"Average:   {result.average:.2f}")
    print(f"Non-crit (parried): {fmt(result.non_crit_parried)}")
    print(f"Crit (parried):     {fmt(result.crit_parried)}")
    print(f"Average w/ parade:  {result.average_with_parade:.2f}")
    print()
    print(f"EM:      {compute_effective_mastery(caster, spell):.0f}")
    print(f"EMcrit:  {compute_effective_mastery(caster, spell, include_crit=True):.0f}")
