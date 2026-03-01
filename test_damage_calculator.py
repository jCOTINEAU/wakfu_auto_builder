"""
Tests for the Wakfu damage calculator.

Run with: python -m pytest test_damage_calculator.py -v
"""

import pytest
from damage_calculator import (
    CasterStats,
    DamageResult,
    Element,
    Orientation,
    Spell,
    StochasticDamage,
    TargetStats,
    compute_damage,
    compute_effective_mastery,
    compute_spell_damage,
    compute_spell_damage_raw,
    flat_res_to_percent,
    percent_res_to_flat,
)


# ---------------------------------------------------------------------------
# Resistance conversion
# ---------------------------------------------------------------------------

class TestResistanceConversion:

    def test_zero_resistance(self):
        assert flat_res_to_percent(0) == 0

    def test_positive_resistance(self):
        # 100 flat -> 1 - 0.8^1 = 0.2 -> 20%
        assert flat_res_to_percent(100) == 20

    def test_high_resistance_capped_at_90(self):
        assert flat_res_to_percent(5000) == 90

    def test_negative_resistance(self):
        pct = flat_res_to_percent(-100)
        assert pct < 0

    def test_roundtrip_100(self):
        pct = flat_res_to_percent(100)  # 20%
        assert pct == 20
        flat_back = percent_res_to_flat(pct)
        assert flat_back == 100

    def test_roundtrip_300(self):
        pct = flat_res_to_percent(300)  # 48%
        assert pct == 48
        flat_back = percent_res_to_flat(pct)
        # ceil(inverse(48%)) = 294 — not 300 because floor is lossy
        assert flat_back == percent_res_to_flat(48)


# ---------------------------------------------------------------------------
# Basic damage computation
# ---------------------------------------------------------------------------

class TestBasicDamage:

    def test_zero_mastery_zero_res(self):
        caster = CasterStats()
        target = TargetStats()
        spell = Spell(base=100)
        dmg = compute_spell_damage(caster, target, spell, is_crit=False)
        assert dmg == 100

    def test_mastery_scaling(self):
        caster = CasterStats(elemental_mastery=100)
        target = TargetStats()
        spell = Spell(base=100)
        dmg = compute_spell_damage(caster, target, spell, is_crit=False)
        # 100 * (1 + 100/100) = 200
        assert dmg == 200

    def test_critical_multiplier(self):
        caster = CasterStats()
        target = TargetStats()
        spell = Spell(base=100, can_crit=True)
        dmg = compute_spell_damage(caster, target, spell, is_crit=True)
        # 100 * 1.25 = 125
        assert dmg == 125

    def test_no_crit_when_spell_cannot_crit(self):
        caster = CasterStats()
        target = TargetStats()
        spell = Spell(base=100, can_crit=False)
        dmg = compute_spell_damage(caster, target, spell, is_crit=True)
        assert dmg == 100

    def test_orientation_side(self):
        caster = CasterStats()
        target = TargetStats()
        spell = Spell(base=100, orientation=Orientation.SIDE)
        dmg = compute_spell_damage(caster, target, spell, is_crit=False)
        assert dmg == 110

    def test_orientation_back(self):
        caster = CasterStats()
        target = TargetStats()
        spell = Spell(base=100, orientation=Orientation.BACK)
        dmg = compute_spell_damage(caster, target, spell, is_crit=False)
        assert dmg == 125

    def test_damage_inflicted_bonus(self):
        caster = CasterStats(damage_inflicted=50)
        target = TargetStats()
        spell = Spell(base=100)
        dmg = compute_spell_damage(caster, target, spell, is_crit=False)
        # 100 * 1.5 = 150
        assert dmg == 150

    def test_parade_reduces_damage(self):
        caster = CasterStats()
        target = TargetStats()
        spell = Spell(base=100)
        dmg = compute_spell_damage(caster, target, spell, is_crit=False, is_parried=True)
        assert dmg == 80

    def test_parade_expert_block(self):
        caster = CasterStats()
        target = TargetStats(has_expert_block=True)
        spell = Spell(base=100)
        dmg = compute_spell_damage(caster, target, spell, is_crit=False, is_parried=True)
        assert dmg == 68

    def test_resistance_reduces_damage(self):
        caster = CasterStats()
        target = TargetStats(elemental_resistance=100)  # 20%
        spell = Spell(base=100)
        dmg = compute_spell_damage(caster, target, spell, is_crit=False)
        # 100 * 0.80 = 80
        assert dmg == 80


# ---------------------------------------------------------------------------
# Composite: compute_damage
# ---------------------------------------------------------------------------

class TestComputeDamage:

    def test_average_with_50_cc(self):
        caster = CasterStats(critical_chance=50)
        target = TargetStats()
        spell = Spell(base=100)
        result = compute_damage(caster, target, spell)
        assert result.non_crit.low == 100
        assert result.crit.low == 125
        assert result.average == pytest.approx(112.5)

    def test_cc_clamped_to_100(self):
        caster = CasterStats(critical_chance=120)
        target = TargetStats()
        spell = Spell(base=100)
        result = compute_damage(caster, target, spell)
        assert result.average == pytest.approx(125.0)

    def test_stochastic_rounding(self):
        caster = CasterStats(damage_inflicted=8)
        target = TargetStats()
        spell = Spell(base=7)
        result = compute_damage(caster, target, spell)
        assert result.non_crit.raw == pytest.approx(7.56)
        assert result.non_crit.low == 7
        assert result.non_crit.high == 8
        assert result.non_crit.chance_high == pytest.approx(0.56)


# ---------------------------------------------------------------------------
# Effective Mastery
# ---------------------------------------------------------------------------

class TestEffectiveMastery:

    def test_em_zero(self):
        caster = CasterStats()
        spell = Spell(base=100)
        em = compute_effective_mastery(caster, spell)
        assert em == pytest.approx(0.0)

    def test_em_basic(self):
        caster = CasterStats(elemental_mastery=1000, damage_inflicted=0)
        spell = Spell(base=100)
        em = compute_effective_mastery(caster, spell)
        # (1100 * 100 / 100) - 100 = 1000
        assert em == pytest.approx(1000.0)

    def test_em_with_di(self):
        caster = CasterStats(elemental_mastery=1000, damage_inflicted=50)
        spell = Spell(base=100)
        em = compute_effective_mastery(caster, spell)
        # (1100 * 150 / 100) - 100 = 1550
        assert em == pytest.approx(1550.0)


# ---------------------------------------------------------------------------
# Placeholder for real in-game values
# ---------------------------------------------------------------------------

class TestRealValues:
    """Tests based on real in-game observations."""

    def test_base7_di8_no_mastery_no_res(self):
        """
        0 mastery, 8% DI, 3% CC, base 7, face, 0 res.
        In-game: observed both 7 and 8 (non-crit) → stochastic rounding.
        Raw = 7 × 1.08 = 7.56 → 56% chance of 8, 44% chance of 7.
        """
        caster = CasterStats(
            elemental_mastery=0,
            damage_inflicted=8,
            critical_chance=3,
        )
        target = TargetStats(elemental_resistance=0)
        spell = Spell(base=7, orientation=Orientation.FRONT)

        result = compute_damage(caster, target, spell)
        assert result.non_crit.raw == pytest.approx(7.56)
        assert result.non_crit.low == 7
        assert result.non_crit.high == 8
        assert result.non_crit.chance_high == pytest.approx(0.56)

    def test_base7_mastery25_di8_back(self):
        """
        25 elem mastery, 8% DI, base 7, back, 0 res.
        In-game: observed 11 and 12 (non-crit).
        """
        caster = CasterStats(elemental_mastery=25, damage_inflicted=8, critical_chance=3)
        target = TargetStats(elemental_resistance=0)
        spell = Spell(base=7, orientation=Orientation.BACK)

        result = compute_damage(caster, target, spell)
        assert result.non_crit.low == 11
        assert result.non_crit.high == 12

    def test_base7_mastery25_di8_face(self):
        """
        25 elem mastery, 8% DI, base 7, face, 0 res.
        In-game: observed 9 and 10 (non-crit).
        """
        caster = CasterStats(elemental_mastery=25, damage_inflicted=8, critical_chance=3)
        target = TargetStats(elemental_resistance=0)
        spell = Spell(base=7, orientation=Orientation.FRONT)

        result = compute_damage(caster, target, spell)
        assert result.non_crit.raw == pytest.approx(9.45)
        assert result.non_crit.low == 9
        assert result.non_crit.high == 10

    def test_base38_distance_di18_face(self):
        """
        140 elem + 120 distance mastery, 18% DI, base 38, face, 0 res.
        In-game: observed 161 and 162 (non-crit).
        """
        caster = CasterStats(
            elemental_mastery=140,
            damage_inflicted=18,
            critical_chance=3,
            distance_mastery=120,
        )
        target = TargetStats(elemental_resistance=0)
        spell = Spell(base=38, orientation=Orientation.FRONT, is_melee=False)

        result = compute_damage(caster, target, spell)
        assert result.non_crit.low == 161
        assert result.non_crit.high == 162

    def test_base38_distance_di43_back_crit(self):
        """
        140 elem + 120 distance mastery, 43% DI, base 38, back, 0 res.
        In-game: observed 244 non-crit, 309 crit.
        Confirms ceil(base × 1.25) intermediate rounding on crit.
        """
        caster = CasterStats(
            elemental_mastery=140,
            damage_inflicted=43,
            critical_chance=3,
            distance_mastery=120,
        )
        target = TargetStats(elemental_resistance=0)
        spell = Spell(base=38, orientation=Orientation.BACK, is_melee=False)

        result = compute_damage(caster, target, spell)
        assert result.non_crit.low == 244
        assert result.non_crit.high == 245
        assert result.crit.low == 308
        assert result.crit.high == 309

    def test_base38_distance_di18_face_60pct_res(self):
        """
        140 elem + 120 distance mastery, 18% DI, base 38, face, 60% res.
        In-game: observed 64 and 65 (non-crit).
        """
        caster = CasterStats(
            elemental_mastery=140,
            damage_inflicted=18,
            critical_chance=3,
            distance_mastery=120,
        )
        target = TargetStats(elemental_resistance=percent_res_to_flat(60))
        spell = Spell(base=38, orientation=Orientation.FRONT, is_melee=False)

        result = compute_damage(caster, target, spell)
        assert result.non_crit.low == 64
        assert result.non_crit.high == 65
