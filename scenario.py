"""
Scenario runner — Monte-Carlo simulation of spell sequences.

Load a JSON scenario describing a base caster, a target, and a sequence of
spell steps (each with optional stat modifiers and orientation). Run N
iterations rolling crit/parade/stochastic rounding and produce aggregated
statistics per step and total.

Usage:
    python scenario.py path/to/scenario.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from dataclasses import dataclass, field, replace, asdict
from pathlib import Path

from damage_calculator import (
    CasterStats,
    Element,
    Orientation,
    Spell,
    TargetStats,
    compute_spell_damage_raw,
)
from effects import SimState, SpellEffects, apply_pre_damage, apply_post_damage


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class StepConfig:
    name: str
    spell: Spell | None = None  # None = marker step (apply_stacks only, no damage)
    orientation: Orientation = Orientation.FRONT
    caster_modifiers: dict[str, int] = field(default_factory=dict)
    target_modifiers: dict[str, int] = field(default_factory=dict)
    spell_effects: SpellEffects = field(default_factory=SpellEffects)
    apply_stacks: dict[str, int] = field(default_factory=dict)  # marker step: add these to state
    is_marker: bool = False
    end_of_turn: bool = False  # marker flag: increment turn counter after this step


@dataclass
class ScenarioConfig:
    caster: CasterStats
    target: TargetStats
    steps: list[StepConfig]
    iterations: int = 1000
    seed: int | None = None
    thresholds: list[int] = field(default_factory=list)
    level: int | None = None
    initial_stacks: dict[str, int] = field(default_factory=dict)  # e.g. {"point_faible": 50}


@dataclass
class StatsSummary:
    min: int
    avg: float
    max: int
    median: float


@dataclass
class ScenarioResult:
    per_step: list[tuple[str, StatsSummary]]
    total: StatsSummary
    histogram: list[tuple[int, int, int]]  # (low, high, count) — total damages
    thresholds: dict[int, float]            # {X: P(total >= X)}
    total_damages: list[int] = field(default_factory=list)  # raw iterations


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def apply_modifiers(base, modifiers: dict[str, int]):
    """Return a copy of `base` with delta modifiers applied field by field."""
    result = replace(base)
    for field_name, delta in modifiers.items():
        if not hasattr(result, field_name):
            raise ValueError(f"Unknown field on {type(base).__name__}: {field_name}")
        setattr(result, field_name, getattr(result, field_name) + delta)
    return result


def simulate_step(
    caster: CasterStats,
    target: TargetStats,
    spell: Spell,
    orientation: Orientation,
    rng: random.Random,
) -> int:
    """Simulate one spell hit with stochastic crit/parade/rounding."""
    cc = min(max(caster.critical_chance + spell.bonus_critical_chance, 0), 100)
    is_crit = rng.random() * 100 < cc

    is_parried = rng.random() * 100 < target.parade_chance

    raw = compute_spell_damage_raw(
        caster, target, spell, is_crit, orientation, is_parried
    )

    low = math.floor(raw)
    high = math.ceil(raw)
    if low == high:
        return low
    return high if rng.random() < (raw - low) else low


def run_scenario(config: ScenarioConfig) -> ScenarioResult:
    """Execute the scenario N times and aggregate results.

    Auto-applies stack effects (point_faible, hemorragie) across steps.
    Manual caster_modifiers / spell_modifiers stack ON TOP of auto effects.
    """
    rng = random.Random(config.seed)
    step_damages: list[list[int]] = [[] for _ in config.steps]
    total_damages: list[int] = []

    for _ in range(config.iterations):
        # Fresh state for each iteration, seeded with initial stacks
        state = SimState(
            caster=replace(config.caster),
            point_faible=config.initial_stacks.get("point_faible", 0),
            hemorragie=config.initial_stacks.get("hemorragie", 0),
        )
        total = 0
        for i, step in enumerate(config.steps):
            if step.is_marker:
                # Marker step: just apply stacks, no damage
                for stack_name, delta in step.apply_stacks.items():
                    if stack_name == "point_faible":
                        state.add_point_faible(delta)
                    elif stack_name == "hemorragie":
                        state.add_hemorragie(delta)
                    else:
                        raise ValueError(f"Unknown stack: {stack_name}")
                if step.end_of_turn:
                    state.tick_end_of_turn()
                step_damages[i].append(0)
                continue

            # 1. Apply manual caster_modifiers on top of base state
            caster = apply_modifiers(state.caster, step.caster_modifiers)
            target = apply_modifiers(config.target, step.target_modifiers)

            # 2. Apply auto pre-damage effects (consume stacks, fire hem application)
            res = apply_pre_damage(state, step.spell, step.spell_effects, step.orientation)

            # 3. Adjust spell/caster with auto-computed bonuses
            effective_spell = replace(step.spell,
                bonus_base_percent=step.spell.bonus_base_percent + res.bonus_base_percent
            )
            effective_caster = replace(caster,
                final_damage=caster.final_damage + res.df_bonus
            )
            # Apply pending buff stat bonuses (e.g., invisibilité +100 DI)
            for stat_name, delta in res.caster_stat_bonuses.items():
                current = getattr(effective_caster, stat_name, None)
                if current is None:
                    raise ValueError(f"Pending buff targets unknown caster field: {stat_name}")
                effective_caster = replace(effective_caster, **{stat_name: current + delta})

            # 4. Compute damage
            dmg = simulate_step(effective_caster, target, effective_spell, step.orientation, rng)
            step_damages[i].append(dmg)
            total += dmg

            # 5. Apply post-damage effects (stacks applied, hem from consumption)
            apply_post_damage(state, step.spell, step.spell_effects, res, step.orientation)
        total_damages.append(total)

    return _aggregate(step_damages, total_damages, config)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def _summary(values: list[int]) -> StatsSummary:
    if not values:
        return StatsSummary(min=0, avg=0.0, max=0, median=0.0)
    return StatsSummary(
        min=min(values),
        avg=sum(values) / len(values),
        max=max(values),
        median=statistics.median(values),
    )


def _histogram(values: list[int], bucket_count: int = 20) -> list[tuple[int, int, int]]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if lo == hi:
        return [(lo, hi, len(values))]
    width = (hi - lo) / bucket_count
    buckets: list[tuple[int, int, int]] = []
    for i in range(bucket_count):
        b_lo = lo + i * width
        b_hi = lo + (i + 1) * width if i < bucket_count - 1 else hi + 1
        count = sum(1 for v in values if b_lo <= v < b_hi)
        buckets.append((int(b_lo), int(b_hi), count))
    # include the max in the last bucket (edge case)
    if buckets and buckets[-1][2] == 0 and hi in values:
        last = buckets[-1]
        buckets[-1] = (last[0], last[1], values.count(hi))
    return buckets


def _thresholds(values: list[int], thresholds: list[int]) -> dict[int, float]:
    if not values or not thresholds:
        return {}
    n = len(values)
    return {x: sum(1 for v in values if v >= x) / n for x in thresholds}


def _aggregate(
    step_damages: list[list[int]],
    total_damages: list[int],
    config: ScenarioConfig,
) -> ScenarioResult:
    per_step = [
        (step.name, _summary(dmgs))
        for step, dmgs in zip(config.steps, step_damages)
    ]
    return ScenarioResult(
        per_step=per_step,
        total=_summary(total_damages),
        histogram=_histogram(total_damages),
        thresholds=_thresholds(total_damages, config.thresholds),
        total_damages=list(total_damages),
    )


# ---------------------------------------------------------------------------
# JSON I/O
# ---------------------------------------------------------------------------

def load_scenario(path: str) -> ScenarioConfig:
    path_obj = Path(path)
    with open(path_obj) as f:
        data = json.load(f)
    caster = CasterStats(**data["caster"])
    target = TargetStats(**data["target"])
    level = data.get("level")
    spells_dir = _resolve_spells_dir(data.get("spells_dir", "test_data/classes"), path_obj)
    steps = [_parse_step(s, level, spells_dir) for s in data["steps"]]
    return ScenarioConfig(
        caster=caster,
        target=target,
        steps=steps,
        iterations=data.get("iterations", 1000),
        seed=data.get("seed"),
        thresholds=data.get("thresholds", []),
        level=level,
        initial_stacks=data.get("initial_stacks", {}),
    )


def _resolve_spells_dir(spells_dir_str: str, scenario_path: Path) -> Path:
    p = Path(spells_dir_str)
    if p.is_absolute() and p.exists():
        return p
    # try relative to scenario file, then cwd
    for candidate in (scenario_path.parent / p, Path.cwd() / p):
        if candidate.exists():
            return candidate.resolve()
    return p  # will fail at spell load with clear error


def load_spell_from_ref(ref: str, level: int, spells_dir: Path) -> tuple[Spell, SpellEffects]:
    try:
        cls, spell_id = ref.split("/", 1)
    except ValueError:
        raise ValueError(f"Invalid spell ref '{ref}': expected format 'Class/id'")
    spell_path = spells_dir / cls / f"{spell_id}.json"
    if not spell_path.exists():
        raise FileNotFoundError(f"Spell JSON not found: {spell_path}")
    with open(spell_path) as f:
        data = json.load(f)
    entries = data.get("damage_per_level", [])
    level_data = next((e for e in entries if e.get("level") == level), None)
    if level_data is None:
        available = [e.get("level") for e in entries]
        raise ValueError(f"Level {level} not found for spell '{ref}'. Available: {available}")
    spell_kwargs = {
        "base": level_data["damage_non_crit"],
        "crit_base": level_data["damage_crit"],
    }
    metadata = data.get("metadata", {})
    for opt_field in ("is_melee", "is_indirect", "can_crit", "cost_ap"):
        if opt_field in metadata:
            spell_kwargs[opt_field] = metadata[opt_field]
    if "element" in metadata:
        spell_kwargs["element"] = Element(metadata["element"])
    effects = SpellEffects.from_dict(data.get("effects"))
    return Spell(**spell_kwargs), effects


def _parse_step(data: dict, level: int | None, spells_dir: Path) -> StepConfig:
    # Marker step: no spell, just apply stacks (end-of-turn effects, etc.)
    if "spell" not in data:
        apply_stacks = data.get("apply_stacks", {})
        if not apply_stacks:
            raise ValueError(
                f"Step '{data.get('name')}' has no 'spell' and no 'apply_stacks' — "
                f"nothing to do"
            )
        return StepConfig(
            name=data.get("name", "<marker>"),
            spell=None,
            apply_stacks=apply_stacks,
            is_marker=True,
            end_of_turn=data.get("end_of_turn", False),
        )

    spell_def = data["spell"]
    effects = SpellEffects()
    if isinstance(spell_def, str):
        if level is None:
            raise ValueError(
                f"Step '{data.get('name')}' uses spell ref '{spell_def}' "
                f"but scenario has no 'level' field"
            )
        spell, effects = load_spell_from_ref(spell_def, level, spells_dir)
    elif isinstance(spell_def, dict):
        # Inline spell: convert element string to enum if present
        if "element" in spell_def and isinstance(spell_def["element"], str):
            spell_def = {**spell_def, "element": Element(spell_def["element"])}
        spell = Spell(**spell_def)
    else:
        raise ValueError(f"Step '{data.get('name')}' has invalid 'spell' field: {spell_def!r}")

    for field_name, value in data.get("spell_modifiers", {}).items():
        if not hasattr(spell, field_name):
            raise ValueError(f"Unknown Spell field in spell_modifiers: {field_name}")
        setattr(spell, field_name, value)

    return StepConfig(
        name=data["name"],
        spell=spell,
        orientation=Orientation(data.get("orientation", "front")),
        caster_modifiers=data.get("caster_modifiers", {}),
        target_modifiers=data.get("target_modifiers", {}),
        spell_effects=effects,
    )


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------

def print_result(result: ScenarioResult) -> None:
    print("=== Per-step stats ===")
    for name, s in result.per_step:
        print(f"  {name}")
        print(f"    min={s.min}  avg={s.avg:.1f}  max={s.max}  median={s.median:.1f}")

    print()
    print("=== Total scenario ===")
    t = result.total
    print(f"  min={t.min}  avg={t.avg:.1f}  max={t.max}  median={t.median:.1f}")

    if result.histogram:
        print()
        print("=== Histogram (total) ===")
        max_count = max(c for _, _, c in result.histogram) or 1
        for lo, hi, count in result.histogram:
            bar = "#" * int(40 * count / max_count)
            print(f"  [{lo:>6} - {hi:>6}) {bar} {count}")

    if result.thresholds:
        print()
        print("=== Thresholds ===")
        for x, p in result.thresholds.items():
            print(f"  P(total >= {x}) = {p:.1%}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def trace_scenario(config: ScenarioConfig) -> None:
    """Print a detailed step-by-step trace showing stacks, applied effects, and damage.
    Uses deterministic expected damage (avg of non-crit + crit weighted by CC)."""
    state = SimState(
        caster=replace(config.caster),
        point_faible=config.initial_stacks.get("point_faible", 0),
        hemorragie=config.initial_stacks.get("hemorragie", 0),
    )
    total = 0.0

    print(f"=== TRACE {'='*56}")
    print(f"Caster base: water={state.caster.water_mastery} air={state.caster.air_mastery} "
          f"fire={state.caster.fire_mastery} earth={state.caster.earth_mastery} | "
          f"melee={state.caster.melee_mastery} back={state.caster.back_mastery}")
    print(f"             CC={state.caster.critical_chance}%  DI={state.caster.damage_inflicted}  "
          f"DF={state.caster.final_damage}")
    print(f"Target: res={config.target.elemental_resistance}  parade={config.target.parade_chance}%")
    print(f"{'='*64}")

    turn = 1
    for i, step in enumerate(config.steps, 1):
        pf_before, hem_before = state.point_faible, state.hemorragie

        if step.is_marker:
            for stack_name, delta in step.apply_stacks.items():
                if stack_name == "point_faible":
                    state.add_point_faible(delta)
                elif stack_name == "hemorragie":
                    state.add_hemorragie(delta)
            if step.end_of_turn:
                state.tick_end_of_turn()
            marker_label = "END OF TURN" if step.end_of_turn else "MARKER"
            print(f"\n[T{turn} step {i}] {step.name}  ({marker_label})")
            print(f"  STATE IN:  pf={pf_before} hem={hem_before}")
            print(f"  apply_stacks: {dict(step.apply_stacks)}")
            print(f"  STATE OUT: pf={state.point_faible} hem={state.hemorragie}")
            if state.pending_buffs:
                print(f"  pending buffs: {[f'cond={b.condition} apply={b.apply} delayed={b.delayed_turns}' for b in state.pending_buffs]}")
            if step.end_of_turn:
                turn += 1
            continue

        caster = apply_modifiers(state.caster, step.caster_modifiers)
        target = apply_modifiers(config.target, step.target_modifiers)

        res = apply_pre_damage(state, step.spell, step.spell_effects, step.orientation)

        effective_spell = replace(step.spell,
            bonus_base_percent=step.spell.bonus_base_percent + res.bonus_base_percent
        )
        effective_caster = replace(caster,
            final_damage=caster.final_damage + res.df_bonus
        )
        for stat_name, delta in res.caster_stat_bonuses.items():
            current = getattr(effective_caster, stat_name, None)
            if current is not None:
                effective_caster = replace(effective_caster, **{stat_name: current + delta})

        # Deterministic expected damage (non_crit and crit)
        nc = compute_spell_damage_raw(effective_caster, target, effective_spell, False, step.orientation, False)
        cr = compute_spell_damage_raw(effective_caster, target, effective_spell, True, step.orientation, False) if effective_spell.can_crit else nc
        cc = min(max(effective_caster.critical_chance + effective_spell.bonus_critical_chance, 0), 100)
        expected = nc * (1 - cc/100) + cr * (cc/100)
        total += expected

        elem = step.spell.element
        mast_elem_val = effective_caster.elemental_mastery_for(elem)

        print(f"\n[T{turn} step {i}] {step.name}")
        print(f"  spell: {elem} base={step.spell.base}/{step.spell.crit_base} "
              f"is_melee={step.spell.is_melee} is_indirect={step.spell.is_indirect}")
        print(f"  orientation: {step.orientation}")
        print(f"  STATE IN:  pf={pf_before} hem={hem_before}")
        applies_desc = dict(step.spell_effects.applies) if step.spell_effects.applies else None
        consumes_desc = step.spell_effects.consumes_stack
        print(f"  effects declared: applies={applies_desc} consumes={consumes_desc}")
        print(f"  auto: bonus_base_percent +{res.bonus_base_percent}  df +{res.df_bonus}  "
              f"(ap_gain={res.ap_gained} hem_post={res.hem_gained_post})")
        if res.caster_stat_bonuses:
            print(f"  buff consumed: {dict(res.caster_stat_bonuses)}")
        manual_cm = dict(step.caster_modifiers) if step.caster_modifiers else None
        manual_sm = {
            k: v for k, v in vars(step.spell).items()
            if k in ("bonus_damage_inflicted", "bonus_mastery", "bonus_critical_mastery",
                     "bonus_critical_chance", "bonus_base_percent") and v
        }
        if manual_cm:
            print(f"  manual caster_modifiers: {manual_cm}")
        if manual_sm:
            print(f"  manual spell bonuses: {manual_sm}")
        print(f"  stats used: mast_elem({elem})={mast_elem_val}  "
              f"DI={effective_caster.damage_inflicted + effective_spell.bonus_damage_inflicted + target.damage_received}  "
              f"DF={effective_caster.final_damage}  "
              f"bonus_base={effective_spell.bonus_base_percent}%")
        print(f"  damage: nc={nc:.1f}  cr={cr:.1f}  expected@CC{cc}%={expected:.1f}")

        apply_post_damage(state, step.spell, step.spell_effects, res, step.orientation)
        print(f"  STATE OUT: pf={state.point_faible} hem={state.hemorragie}")

    print(f"\n{'='*64}")
    print(f"TOTAL expected damage: {total:.1f}")


def result_to_json(result: ScenarioResult, config: ScenarioConfig, name: str) -> dict:
    return {
        "name": name,
        "iterations": config.iterations,
        "seed": config.seed,
        "per_step": [
            {"name": n, "summary": asdict(s)} for n, s in result.per_step
        ],
        "total_summary": asdict(result.total),
        "total_damages": result.total_damages,
        "thresholds": {str(k): v for k, v in result.thresholds.items()},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a scenario Monte-Carlo simulation")
    parser.add_argument("scenario", help="Path to scenario JSON file")
    parser.add_argument("--json", action="store_true", help="Output structured JSON to stdout (pipe into compare.py)")
    parser.add_argument("--name", help="Override scenario name in JSON output (default: filename stem)")
    parser.add_argument("--trace", action="store_true", help="Print step-by-step trace of stacks and effects")
    args = parser.parse_args()

    config = load_scenario(args.scenario)

    if args.trace:
        trace_scenario(config)
    else:
        result = run_scenario(config)
        if args.json:
            name = args.name or Path(args.scenario).stem
            print(json.dumps(result_to_json(result, config, name)))
        else:
            print_result(result)
