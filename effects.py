"""
Effect system — stack tracking and auto-application across scenario steps.

Manages numerical stacks (point_faible, hemorragie) that persist across spell casts.
Each spell declares what stacks it applies/consumes in its JSON metadata, and this
module auto-applies them, computing bonus_base_percent and final_damage bonuses.

Hors scope Phase A : AP tracking, turn-based state, conditional combos.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

from damage_calculator import CasterStats, Orientation, Spell


POINT_FAIBLE_CAP = 100
HEMORRAGIE_CAP = 40


@dataclass
class SpellEffects:
    """Declarative effects from a spell's JSON metadata.

    JSON schema:
      "effects": {
        "applies":  { "point_faible": 10, "hemorragie": 20 },
        "consumes": { "stack": "point_faible" },
        "arm_buff": {                          # delayed caster buff, consumed by first matching spell
          "condition": { "min_ap": 4 },
          "apply":     { "damage_inflicted": 100 },
          "delayed_turns": 1                   # 0 = next spell, 1 = after next end-of-turn
        },
        "recast_at_next_turn_start": {         # auto-fire self at next end-of-turn
          "orientation": "front",              # worst-case orientation for the recast
          "is_melee": false                    # worst-case range flag
        }
      }

    `applies` values can be:
      - int: unconditional value
      - dict by orientation: {"front": 10, "side": 10, "back": 15}
    """
    applies: dict[str, int | dict] = field(default_factory=dict)
    consumes_stack: Optional[str] = None  # "point_faible" | "hemorragie" | None
    arm_buff: Optional[dict] = None        # {condition, apply, delayed_turns}
    recast_at_next_turn_start: Optional[dict] = None  # {orientation, is_melee}

    @classmethod
    def from_dict(cls, data: dict | None) -> SpellEffects:
        if not data:
            return cls()
        consumes = data.get("consumes") or {}
        return cls(
            applies=dict(data.get("applies") or {}),
            consumes_stack=consumes.get("stack"),
            arm_buff=data.get("arm_buff"),
            recast_at_next_turn_start=data.get("recast_at_next_turn_start"),
        )

    def applies_value(self, stack: str, orientation: Orientation) -> int:
        raw = self.applies.get(stack, 0)
        if isinstance(raw, dict):
            return int(raw.get(str(orientation), raw.get("front", 0)))
        return int(raw)


@dataclass
class PendingBuff:
    """Delayed conditional caster buff.

    `condition`: dict of filters the spell must match (e.g. {"min_ap": 4}).
    `apply`:     dict of caster stat deltas to add when triggered (e.g. {"damage_inflicted": 100}).
    `delayed_turns`: turns until the buff is armed (0 = immediately next cast; 1 = after next end-of-turn).
    `max_triggers`: number of times the buff can fire before being removed (default 1).
    """
    condition: dict
    apply: dict
    delayed_turns: int = 0
    max_triggers: int = 1

    def is_armed(self) -> bool:
        return self.delayed_turns <= 0 and self.max_triggers > 0

    def matches(self, spell) -> bool:
        c = self.condition or {}
        if "min_ap" in c and getattr(spell, "cost_ap", 0) < c["min_ap"]:
            return False
        return True


@dataclass
class ScheduledCast:
    """Spell scheduled to fire automatically at start of next turn (consumed on end_of_turn)."""
    spell: Spell
    effects: SpellEffects
    orientation: Orientation


@dataclass
class SimState:
    """State carried across scenario steps."""
    caster: CasterStats
    point_faible: int = 0
    hemorragie: int = 0
    pending_buffs: list[PendingBuff] = field(default_factory=list)
    scheduled_casts: list[ScheduledCast] = field(default_factory=list)
    # Phase B: ap: int = 0

    def add_point_faible(self, value: int) -> None:
        self.point_faible = min(self.point_faible + value, POINT_FAIBLE_CAP)
        self.point_faible = max(self.point_faible, 0)

    def add_hemorragie(self, value: int) -> None:
        self.hemorragie = min(self.hemorragie + value, HEMORRAGIE_CAP)
        self.hemorragie = max(self.hemorragie, 0)

    def consume_point_faible(self) -> int:
        """Consume all pf, return amount consumed."""
        consumed = self.point_faible
        self.point_faible = 0
        return consumed

    def consume_hemorragie(self) -> int:
        """Consume all hem, return amount consumed."""
        consumed = self.hemorragie
        self.hemorragie = 0
        return consumed

    def tick_end_of_turn(self) -> None:
        """Decrement delayed_turns on all pending buffs."""
        for buff in self.pending_buffs:
            if buff.delayed_turns > 0:
                buff.delayed_turns -= 1

    def consume_matching_buffs(self, spell) -> dict:
        """Apply first matching armed buff's effect, consume it. Returns aggregated apply dict."""
        result: dict[str, int] = {}
        remaining: list[PendingBuff] = []
        consumed_one = False
        for buff in self.pending_buffs:
            if not consumed_one and buff.is_armed() and buff.matches(spell):
                for k, v in buff.apply.items():
                    result[k] = result.get(k, 0) + v
                buff.max_triggers -= 1
                consumed_one = True
                if buff.max_triggers > 0:
                    remaining.append(buff)
            else:
                remaining.append(buff)
        self.pending_buffs = remaining
        return result


def point_faible_threshold_bonus(consumed: int) -> tuple[int, int]:
    """Return (ap_gained, hem_gained) for a given pf consumption amount.

    Thresholds (à confirmer):
      >=  25 : +1 AP, +10 hem
      >=  50 : +2 AP, +20 hem
      >=  75 : +3 AP, +30 hem
      == 100 : +4 AP, +100 hem  (cap special case)
    """
    if consumed >= 100:
        return (4, 100)
    if consumed >= 75:
        return (3, 30)
    if consumed >= 50:
        return (2, 20)
    if consumed >= 25:
        return (1, 10)
    return (0, 0)


@dataclass
class StepResolution:
    """Result of applying effects for a single step, fed to the damage engine."""
    bonus_base_percent: int = 0    # from pf consumption
    df_bonus: int = 0               # from hemorragie passive (if spell is direct)
    caster_stat_bonuses: dict[str, int] = field(default_factory=dict)  # from pending buffs
    # Kept for Phase B:
    ap_gained: int = 0
    hem_gained_post: int = 0        # hem to apply AFTER damage


def apply_pre_damage(
    state: SimState,
    spell: Spell,
    effects: SpellEffects,
    orientation: Orientation,
) -> StepResolution:
    """Apply effects that happen before the damage calculation.

    Returns bonuses to feed into the damage calc.
    """
    res = StepResolution()

    # 1. Fire spells: apply hemorragie BEFORE hit (the spell itself benefits)
    if spell.element == "fire" and "hemorragie" in effects.applies:
        state.add_hemorragie(effects.applies_value("hemorragie", orientation))

    # 2. Consume point_faible → bonus_base_percent
    if effects.consumes_stack == "point_faible":
        consumed = state.consume_point_faible()
        res.bonus_base_percent = consumed
        ap, hem = point_faible_threshold_bonus(consumed)
        res.ap_gained = ap
        res.hem_gained_post = hem  # applied AFTER damage

    # 3. Consume hemorragie → point_faible (ouvrir: 1 PF per hem level)
    elif effects.consumes_stack == "hemorragie":
        consumed = state.consume_hemorragie()
        state.add_point_faible(consumed)

    # 4. Hemorragie passive DF: direct spells gain +hem% DF
    if not spell.is_indirect:
        res.df_bonus = state.hemorragie

    # 5. Consume first matching pending buff (e.g. invisibilité's +100 DI on 4+AP spell)
    res.caster_stat_bonuses = state.consume_matching_buffs(spell)

    # 6. Arm a new buff if this spell declares one (post-consume so it doesn't trigger itself)
    if effects.arm_buff:
        ab = effects.arm_buff
        state.pending_buffs.append(PendingBuff(
            condition=ab.get("condition", {}),
            apply=ab.get("apply", {}),
            delayed_turns=ab.get("delayed_turns", 0),
            max_triggers=ab.get("max_triggers", 1),
        ))

    return res


def apply_post_damage(
    state: SimState,
    spell: Spell,
    effects: SpellEffects,
    res: StepResolution,
    orientation: Orientation,
) -> None:
    """Apply effects that happen after the damage hits (stacks that don't boost the spell itself)."""

    # 1. Non-fire spells that apply hemorragie (applied after damage)
    if spell.element != "fire" and "hemorragie" in effects.applies:
        state.add_hemorragie(effects.applies_value("hemorragie", orientation))

    # 2. Point_faible application (always post-damage)
    if "point_faible" in effects.applies:
        state.add_point_faible(effects.applies_value("point_faible", orientation))

    # 3. Hem generated from pf consumption (post-damage per user spec)
    if res.hem_gained_post:
        state.add_hemorragie(res.hem_gained_post)

    # 4. Schedule re-cast at next turn start (e.g. Saignée re-casts next turn)
    if effects.recast_at_next_turn_start:
        cfg = effects.recast_at_next_turn_start
        # Build a modified spell with worst-case orientation/melee flags
        recast_spell = spell
        if "is_melee" in cfg:
            recast_spell = replace(recast_spell, is_melee=cfg["is_melee"])
        recast_orient = Orientation(cfg.get("orientation", "front"))
        state.scheduled_casts.append(ScheduledCast(
            spell=recast_spell, effects=effects, orientation=recast_orient
        ))
