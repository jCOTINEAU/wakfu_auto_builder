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
