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
    Orientation,
    Spell,
    TargetStats,
    compute_spell_damage_raw,
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class StepConfig:
    name: str
    spell: Spell
    orientation: Orientation = Orientation.FRONT
    caster_modifiers: dict[str, int] = field(default_factory=dict)
    target_modifiers: dict[str, int] = field(default_factory=dict)


@dataclass
class ScenarioConfig:
    caster: CasterStats
    target: TargetStats
    steps: list[StepConfig]
    iterations: int = 1000
    seed: int | None = None
    thresholds: list[int] = field(default_factory=list)
    level: int | None = None


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
    """Execute the scenario N times and aggregate results."""
    rng = random.Random(config.seed)
    step_damages: list[list[int]] = [[] for _ in config.steps]
    total_damages: list[int] = []

    for _ in range(config.iterations):
        total = 0
        for i, step in enumerate(config.steps):
            caster = apply_modifiers(config.caster, step.caster_modifiers)
            target = apply_modifiers(config.target, step.target_modifiers)
            dmg = simulate_step(caster, target, step.spell, step.orientation, rng)
            step_damages[i].append(dmg)
            total += dmg
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


def load_spell_from_ref(ref: str, level: int, spells_dir: Path) -> Spell:
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
    for opt_field in ("is_melee", "is_indirect", "can_crit"):
        if opt_field in metadata:
            spell_kwargs[opt_field] = metadata[opt_field]
    return Spell(**spell_kwargs)


def _parse_step(data: dict, level: int | None, spells_dir: Path) -> StepConfig:
    spell_def = data["spell"]
    if isinstance(spell_def, str):
        if level is None:
            raise ValueError(
                f"Step '{data.get('name')}' uses spell ref '{spell_def}' "
                f"but scenario has no 'level' field"
            )
        spell = load_spell_from_ref(spell_def, level, spells_dir)
    elif isinstance(spell_def, dict):
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
    args = parser.parse_args()

    config = load_scenario(args.scenario)
    result = run_scenario(config)

    if args.json:
        name = args.name or Path(args.scenario).stem
        print(json.dumps(result_to_json(result, config, name)))
    else:
        print_result(result)
