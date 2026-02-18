"""Tests for solver.py — pure helper functions and constraint builders."""

import settings
from settings import simpleActionEnum, eqTypeEnum, rarityEnum, paramsActionEnum
from solver import (
    safeget,
    getEquipEffectValue,
    getEquipmentType,
    getWaeponType,
    getRarity,
    getEquipEffectValueWithParams,
    getLevel,
    createConstraintWithFunc,
    createSimpleAddSubstractConstraint,
    createParamsConstraint,
    createLevelConstraint,
)
from ortools.linear_solver import pywraplp
from tests.conftest import make_item


# ---------------------------------------------------------------------------
# safeget
# ---------------------------------------------------------------------------

class TestSafeget:

    def test_existing_nested_key(self):
        d = {"a": {"b": {"c": 42}}}
        assert safeget(d, "a", "b", "c") == 42

    def test_missing_key_returns_none(self):
        d = {"a": {"b": 1}}
        assert safeget(d, "a", "x") is None

    def test_empty_keys_returns_dict(self):
        d = {"a": 1}
        assert safeget(d) == {"a": 1}

    def test_deeply_nested(self):
        d = {"definition": {"equipEffects": {20: {"effect": {"definition": {"params": [100, 2]}}}}}}
        assert safeget(d, "definition", "equipEffects", 20, "effect", "definition", "params") == [100, 2]


# ---------------------------------------------------------------------------
# getEquipEffectValue
# ---------------------------------------------------------------------------

class TestGetEquipEffectValue:

    def test_returns_param0_plus_param1_times_50(self, sample_item):
        result = getEquipEffectValue(sample_item, int(simpleActionEnum.PV_ADD))
        assert result == 100  # params=[100, 0] -> 100 + 0*50 = 100

    def test_with_nonzero_param1(self):
        item = make_item(1, 100, 134, 4, effects={20: [10, 2]})
        result = getEquipEffectValue(item, 20)
        assert result == 110  # 10 + 2*50 = 110

    def test_missing_effect_returns_zero(self, sample_item):
        assert getEquipEffectValue(sample_item, 9999) == 0


# ---------------------------------------------------------------------------
# getEquipEffectValueWithParams
# ---------------------------------------------------------------------------

class TestGetEquipEffectValueWithParams:

    def test_ratio_greater_than_or_equal_param2(self, sample_item_with_params):
        action_id = int(paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD)
        result = getEquipEffectValueWithParams(sample_item_with_params, action_id, ratio=3)
        assert result == 90  # params=[30,0,3], ratio>=3 -> 30*3=90

    def test_ratio_greater_than_param2(self, sample_item_with_params):
        action_id = int(paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD)
        result = getEquipEffectValueWithParams(sample_item_with_params, action_id, ratio=5)
        assert result == 90  # ratio(5) >= param2(3) -> 30*3=90

    def test_ratio_less_than_param2(self, sample_item_with_params):
        action_id = int(paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD)
        result = getEquipEffectValueWithParams(sample_item_with_params, action_id, ratio=2)
        assert result == 60  # ratio(2) < param2(3) -> 30*2=60

    def test_missing_effect_returns_zero(self, sample_item_with_params):
        assert getEquipEffectValueWithParams(sample_item_with_params, 9999) == 0


# ---------------------------------------------------------------------------
# getEquipmentType
# ---------------------------------------------------------------------------

class TestGetEquipmentType:

    def test_matching_type(self, sample_item):
        assert getEquipmentType(sample_item, int(eqTypeEnum.HEAD)) == 1

    def test_non_matching_type(self, sample_item):
        assert getEquipmentType(sample_item, int(eqTypeEnum.CHEST)) == 0


# ---------------------------------------------------------------------------
# getWaeponType
# ---------------------------------------------------------------------------

class TestGetWaeponType:

    def test_primary_weapon(self):
        item = make_item(1, 100, 518, 4, weapon_flags={"isPrimary": 1})
        assert getWaeponType(item, "isPrimary") == 1

    def test_not_a_weapon(self, sample_item):
        assert getWaeponType(sample_item, "isPrimary") == 0

    def test_two_handed(self):
        item = make_item(1, 100, 518, 4, weapon_flags={"isTwoHanded": 1})
        assert getWaeponType(item, "isTwoHanded") == 1


# ---------------------------------------------------------------------------
# getRarity
# ---------------------------------------------------------------------------

class TestGetRarity:

    def test_matching_rarity(self, sample_item):
        assert getRarity(sample_item, int(rarityEnum.LEGENDARY)) == 1

    def test_non_matching_rarity(self, sample_item):
        assert getRarity(sample_item, int(rarityEnum.WHITE)) == 0


# ---------------------------------------------------------------------------
# getLevel
# ---------------------------------------------------------------------------

class TestGetLevel:

    def test_returns_level(self, sample_item):
        assert getLevel(sample_item) == 200

    def test_missing_level_returns_zero(self):
        item = {"definition": {"item": {}}}
        assert getLevel(item) == 0


# ---------------------------------------------------------------------------
# createConstraintWithFunc / createSimpleAddSubstractConstraint
# (require solver variables to be set up)
# ---------------------------------------------------------------------------

class TestConstraintBuilders:

    def _setup_solver_with_items(self, items_dict):
        """Set up a solver, populate settings.ITEMS_DATA and settings.VARIABLES."""
        solver = pywraplp.Solver("test", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.ITEMS_DATA = items_dict
        settings.VARIABLES = {}
        for key, item in items_dict.items():
            settings.VARIABLES[key] = solver.BoolVar(f"item_{key}")
        return solver

    def test_createConstraintWithFunc_basic(self, sample_item):
        items = {1001: sample_item}
        solver = self._setup_solver_with_items(items)

        expr = createConstraintWithFunc(getEquipEffectValue, int(simpleActionEnum.PV_ADD))
        # Expression should be: var_1001 * 100
        # Force the variable to 1 and check objective
        solver.Maximize(expr)
        solver.Add(settings.VARIABLES[1001] == 1)
        solver.Solve()
        assert solver.Objective().Value() == 100

    def test_createSimpleAddSubstractConstraint(self):
        item = make_item(1, 100, 134, 4, effects={
            int(simpleActionEnum.PV_ADD): [200, 0],
            int(simpleActionEnum.PV_MINUS): [50, 0],
        })
        items = {1: item}
        solver = self._setup_solver_with_items(items)

        expr = createSimpleAddSubstractConstraint(simpleActionEnum.PV_ADD, simpleActionEnum.PV_MINUS)
        solver.Maximize(expr)
        solver.Add(settings.VARIABLES[1] == 1)
        solver.Solve()
        assert solver.Objective().Value() == 150  # 200 - 50

    def test_createParamsConstraint(self):
        item = make_item(1, 100, 134, 4, effects={
            int(paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD): [30, 0, 3],
        })
        items = {1: item}
        solver = self._setup_solver_with_items(items)

        expr = createParamsConstraint(
            paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD,
            paramsActionEnum.RANDOM_NUMBER_MASTERY_MINUS,
            ratio=3,
        )
        solver.Maximize(expr)
        solver.Add(settings.VARIABLES[1] == 1)
        solver.Solve()
        assert solver.Objective().Value() == 90  # 30*3

    def test_createLevelConstraint(self):
        item_high = make_item(1, 200, 134, 4)
        item_low = make_item(2, 50, 134, 4)
        items = {1: item_high, 2: item_low}
        solver = self._setup_solver_with_items(items)

        expr = createLevelConstraint(100)
        # Only item 1 has level >= 100
        solver.Maximize(expr)
        solver.Solve()
        assert solver.Objective().Value() == 1  # only item_high selected


# ---------------------------------------------------------------------------
# Mastery scaling in objective function
# Reproduces the ELEM_MASTERY_ADD bug: universal mastery must be scaled
# by nbElem (number of selected elements) in the objective.
# ---------------------------------------------------------------------------

class TestMasteryScaling:
    """Test that ELEM_MASTERY_ADD is properly weighted vs single-element mastery."""

    def _setup_solver_with_items(self, items_dict):
        solver = pywraplp.Solver("test", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.ITEMS_DATA = items_dict
        settings.VARIABLES = {}
        for key, item in items_dict.items():
            settings.VARIABLES[key] = solver.BoolVar(f"item_{key}")
        return solver

    def test_elem_mastery_objective_coefficient_scales_with_nbelem(self):
        """ELEM_MASTERY_ADD +100 with nbElem=2 should contribute 200 to the objective."""
        item = make_item(1, 100, 134, 4, effects={
            int(simpleActionEnum.ELEM_MASTERY_ADD): [100, 0],
        })
        items = {1: item}
        solver = self._setup_solver_with_items(items)

        nbElem = 2
        expr = createSimpleAddSubstractConstraint(
            simpleActionEnum.ELEM_MASTERY_ADD,
            simpleActionEnum.ELEM_MASTERY_MINUS,
        ) * nbElem

        solver.Maximize(expr)
        solver.Add(settings.VARIABLES[1] == 1)
        solver.Solve()
        assert solver.Objective().Value() == 200  # 100 * 2 elements

    def test_elem_mastery_beats_single_element_for_two_elements(self):
        """When optimizing for 2 elements, +100 ELEM_MASTERY (worth 200)
        should beat +100 single-element FIRE_MASTERY (worth 100).

        Two daggers in the same slot — solver must pick the elemental one.
        """
        # Dagger A: +100 fire mastery only
        dagger_fire = make_item(1, 100, 518, 4, effects={
            int(simpleActionEnum.FIRE_MASTERY_ADD): [100, 0],
        }, title="Dague Piou", weapon_flags={"isPrimary": 1})

        # Dagger B: +100 elemental mastery (all 4 elements)
        dagger_elem = make_item(2, 100, 518, 4, effects={
            int(simpleActionEnum.ELEM_MASTERY_ADD): [100, 0],
        }, title="Dague Elementaire", weapon_flags={"isPrimary": 1})

        items = {1: dagger_fire, 2: dagger_elem}
        solver = self._setup_solver_with_items(items)

        # Only one primary weapon allowed
        solver.Add(settings.VARIABLES[1] + settings.VARIABLES[2] <= 1)
        # Must pick one
        solver.Add(settings.VARIABLES[1] + settings.VARIABLES[2] >= 1)

        nbElem = 2  # optimizing fire + water

        # Build the objective like wakfuConstraintSelector does:
        # fire mastery (selected)
        maximize = createSimpleAddSubstractConstraint(
            simpleActionEnum.FIRE_MASTERY_ADD, simpleActionEnum.FIRE_MASTERY_MINUS)
        # water mastery (selected) — neither dagger has it, but included for completeness
        maximize += createSimpleAddSubstractConstraint(
            simpleActionEnum.WATER_MASTERY_ADD, simpleActionEnum.WATER_MASTERY_MINUS)
        # elem mastery — THIS is the line under test: must be * nbElem
        maximize += createSimpleAddSubstractConstraint(
            simpleActionEnum.ELEM_MASTERY_ADD, simpleActionEnum.ELEM_MASTERY_MINUS) * nbElem

        solver.Maximize(maximize)
        solver.Solve()

        # Dagger elem should win: 100*2=200 vs fire dagger: 100
        assert settings.VARIABLES[2].solution_value() == 1, \
            "Solver should pick the elemental mastery dagger"
        assert settings.VARIABLES[1].solution_value() == 0

    def test_elem_mastery_equal_to_single_for_one_element(self):
        """When optimizing for 1 element only, +100 ELEM_MASTERY and
        +100 single-element FIRE_MASTERY are equivalent (both worth 100).
        """
        dagger_fire = make_item(1, 100, 518, 4, effects={
            int(simpleActionEnum.FIRE_MASTERY_ADD): [100, 0],
        }, title="Dague Piou", weapon_flags={"isPrimary": 1})

        dagger_elem = make_item(2, 100, 518, 4, effects={
            int(simpleActionEnum.ELEM_MASTERY_ADD): [100, 0],
        }, title="Dague Elementaire", weapon_flags={"isPrimary": 1})

        items = {1: dagger_fire, 2: dagger_elem}
        solver = self._setup_solver_with_items(items)

        solver.Add(settings.VARIABLES[1] + settings.VARIABLES[2] <= 1)
        solver.Add(settings.VARIABLES[1] + settings.VARIABLES[2] >= 1)

        nbElem = 1  # fire only

        maximize = createSimpleAddSubstractConstraint(
            simpleActionEnum.FIRE_MASTERY_ADD, simpleActionEnum.FIRE_MASTERY_MINUS)
        maximize += createSimpleAddSubstractConstraint(
            simpleActionEnum.ELEM_MASTERY_ADD, simpleActionEnum.ELEM_MASTERY_MINUS) * nbElem

        solver.Maximize(maximize)
        solver.Solve()

        # Both are worth 100 — solver picks either, just check objective = 100
        assert solver.Objective().Value() == 100

    def test_tri_element_vs_elem_mastery_for_two_elements(self):
        """Reproduces the actual user bug: tri-element mastery (RANDOM_NUMBER,
        params[2]=3) with +50/element vs elemental mastery +100 all 4 elements.

        Optimizing for 2 elements:
        - Tri-element: min(2, 3) * 50 = 100
        - Elemental:   100 * 2 = 200

        The elemental dagger should win.
        """
        # Dague piou: mastery in 3 elements, +50 per element
        dague_piou = make_item(1, 100, 518, 4, effects={
            int(paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD): [50, 0, 3],
        }, title="Dague Piou", weapon_flags={"isPrimary": 1})

        # Better dagger: +100 elemental mastery (all 4)
        dague_elem = make_item(2, 100, 518, 4, effects={
            int(simpleActionEnum.ELEM_MASTERY_ADD): [100, 0],
        }, title="Dague Elementaire", weapon_flags={"isPrimary": 1})

        items = {1: dague_piou, 2: dague_elem}
        solver = self._setup_solver_with_items(items)

        solver.Add(settings.VARIABLES[1] + settings.VARIABLES[2] <= 1)
        solver.Add(settings.VARIABLES[1] + settings.VARIABLES[2] >= 1)

        nbElem = 2

        # Build objective as wakfuConstraintSelector should:
        maximize = createParamsConstraint(
            paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD,
            paramsActionEnum.RANDOM_NUMBER_MASTERY_MINUS,
            nbElem)
        maximize += createSimpleAddSubstractConstraint(
            simpleActionEnum.ELEM_MASTERY_ADD,
            simpleActionEnum.ELEM_MASTERY_MINUS) * nbElem

        solver.Maximize(maximize)
        solver.Solve()

        # Elem dagger (200) should beat tri-element piou (100)
        assert settings.VARIABLES[2].solution_value() == 1, \
            "Solver should pick elemental mastery dagger over tri-element"
