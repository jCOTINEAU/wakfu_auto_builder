"""
Structural tests for the scenario runner.

Only structural/plumbing tests here — behavioral tests on damage values
must be validated with the user before being added.

Run with: python -m pytest test_scenario.py -v
"""

import json
import os
import tempfile

import pytest

from damage_calculator import CasterStats, Orientation, Spell, TargetStats
from scenario import (
    ScenarioConfig,
    StepConfig,
    apply_modifiers,
    load_scenario,
    run_scenario,
)


# ---------------------------------------------------------------------------
# apply_modifiers
# ---------------------------------------------------------------------------

class TestApplyModifiers:

    def test_no_modifiers(self):
        base = CasterStats(damage_inflicted=50)
        result = apply_modifiers(base, {})
        assert result.damage_inflicted == 50
        assert result is not base  # copy, not the same object

    def test_single_delta(self):
        base = CasterStats(damage_inflicted=50)
        result = apply_modifiers(base, {"damage_inflicted": 18})
        assert result.damage_inflicted == 68

    def test_negative_delta(self):
        base = CasterStats(damage_inflicted=50)
        result = apply_modifiers(base, {"damage_inflicted": -12})
        assert result.damage_inflicted == 38

    def test_multiple_fields(self):
        base = CasterStats(damage_inflicted=50, melee_mastery=287, back_mastery=145)
        result = apply_modifiers(base, {"damage_inflicted": 10, "melee_mastery": -50})
        assert result.damage_inflicted == 60
        assert result.melee_mastery == 237
        assert result.back_mastery == 145  # untouched

    def test_base_not_mutated(self):
        base = CasterStats(damage_inflicted=50)
        apply_modifiers(base, {"damage_inflicted": 100})
        assert base.damage_inflicted == 50  # original unchanged

    def test_unknown_field_raises(self):
        base = CasterStats()
        with pytest.raises(ValueError, match="Unknown field"):
            apply_modifiers(base, {"not_a_real_field": 10})

    def test_works_on_target(self):
        base = TargetStats(elemental_resistance=100)
        result = apply_modifiers(base, {"elemental_resistance": -50})
        assert result.elemental_resistance == 50


# ---------------------------------------------------------------------------
# load_scenario (JSON parsing)
# ---------------------------------------------------------------------------

class TestLoadScenario:

    def _write_tmp(self, data: dict) -> str:
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        return path

    def test_minimal(self):
        data = {
            "caster": {},
            "target": {},
            "steps": [],
        }
        path = self._write_tmp(data)
        config = load_scenario(path)
        assert isinstance(config.caster, CasterStats)
        assert isinstance(config.target, TargetStats)
        assert config.steps == []
        assert config.iterations == 1000  # default
        assert config.seed is None
        assert config.thresholds == []

    def test_full(self):
        data = {
            "iterations": 500,
            "seed": 42,
            "caster": {"damage_inflicted": 50},
            "target": {"elemental_resistance": 100},
            "steps": [
                {
                    "name": "Sort A",
                    "spell": {"base": 48, "crit_multiplier": 1.2375},
                    "orientation": "back",
                    "caster_modifiers": {"damage_inflicted": 18},
                    "target_modifiers": {"elemental_resistance": -50},
                }
            ],
            "thresholds": [1000, 2000],
        }
        path = self._write_tmp(data)
        config = load_scenario(path)
        assert config.iterations == 500
        assert config.seed == 42
        assert config.caster.damage_inflicted == 50
        assert config.target.elemental_resistance == 100
        assert config.thresholds == [1000, 2000]
        assert len(config.steps) == 1
        step = config.steps[0]
        assert step.name == "Sort A"
        assert step.spell.base == 48
        assert step.spell.crit_multiplier == 1.2375
        assert step.orientation == Orientation.BACK
        assert step.caster_modifiers == {"damage_inflicted": 18}
        assert step.target_modifiers == {"elemental_resistance": -50}

    def test_default_orientation_is_front(self):
        data = {
            "caster": {},
            "target": {},
            "steps": [{"name": "x", "spell": {"base": 10}}],
        }
        path = self._write_tmp(data)
        config = load_scenario(path)
        assert config.steps[0].orientation == Orientation.FRONT


# ---------------------------------------------------------------------------
# run_scenario (plumbing)
# ---------------------------------------------------------------------------

class TestRunScenario:

    def test_reproducible_with_seed(self):
        """Same seed + same config → identical result."""
        config = ScenarioConfig(
            caster=CasterStats(elemental_mastery=100, critical_chance=30),
            target=TargetStats(parade_chance=20),
            steps=[StepConfig(name="s", spell=Spell(base=50))],
            iterations=200,
            seed=42,
        )
        r1 = run_scenario(config)
        r2 = run_scenario(config)
        assert r1.total.min == r2.total.min
        assert r1.total.max == r2.total.max
        assert r1.total.avg == r2.total.avg
        assert r1.total.median == r2.total.median

    def test_different_seed_different_result(self):
        """Different seeds (probably) give different results."""
        base = dict(
            caster=CasterStats(critical_chance=50),
            target=TargetStats(),
            steps=[StepConfig(name="s", spell=Spell(base=50))],
            iterations=100,
        )
        r1 = run_scenario(ScenarioConfig(**base, seed=1))
        r2 = run_scenario(ScenarioConfig(**base, seed=2))
        # avg is very unlikely to be identical across different seeds
        assert r1.total.avg != r2.total.avg

    def test_zero_iterations(self):
        config = ScenarioConfig(
            caster=CasterStats(),
            target=TargetStats(),
            steps=[StepConfig(name="s", spell=Spell(base=50))],
            iterations=0,
            seed=0,
        )
        result = run_scenario(config)
        assert result.total.min == 0
        assert result.total.avg == 0.0
        assert result.total.max == 0
        assert result.per_step[0][1].min == 0

    def test_zero_steps(self):
        config = ScenarioConfig(
            caster=CasterStats(),
            target=TargetStats(),
            steps=[],
            iterations=10,
            seed=0,
        )
        result = run_scenario(config)
        assert result.per_step == []
        # total_damages is filled with 0s (no steps = no damage each iter)
        assert result.total.min == 0
        assert result.total.max == 0

    def test_per_step_names_preserved(self):
        config = ScenarioConfig(
            caster=CasterStats(),
            target=TargetStats(),
            steps=[
                StepConfig(name="first", spell=Spell(base=10)),
                StepConfig(name="second", spell=Spell(base=20)),
            ],
            iterations=5,
            seed=0,
        )
        result = run_scenario(config)
        names = [name for name, _ in result.per_step]
        assert names == ["first", "second"]

    def test_thresholds_in_result(self):
        config = ScenarioConfig(
            caster=CasterStats(),
            target=TargetStats(),
            steps=[StepConfig(name="s", spell=Spell(base=100))],
            iterations=50,
            seed=0,
            thresholds=[50, 150],
        )
        result = run_scenario(config)
        # 50 should be exceeded (base 100, no modifiers), 150 should not
        assert result.thresholds[50] == 1.0
        assert result.thresholds[150] == 0.0

    def test_step_modifiers_are_not_persistent(self):
        """Step N modifiers must not leak to step N+1 (base + modifier only)."""
        config = ScenarioConfig(
            caster=CasterStats(damage_inflicted=0),
            target=TargetStats(),
            steps=[
                StepConfig(
                    name="with_boost",
                    spell=Spell(base=100),
                    caster_modifiers={"damage_inflicted": 100},
                ),
                StepConfig(
                    name="no_boost",
                    spell=Spell(base=100),
                ),
            ],
            iterations=1,
            seed=0,
        )
        result = run_scenario(config)
        _, boosted = result.per_step[0]
        _, plain = result.per_step[1]
        # boosted step should do more damage than plain step
        # (DI 100% = x2 vs DI 0% = x1, no crit since cc=0)
        assert boosted.min > plain.min
        # plain step should match base value (no modifier applied to it)
        # raw = 100 * 1.0 * 1.0 * 1.0 = 100 → stochastic 100 or 100
        assert plain.min == 100 and plain.max == 100
