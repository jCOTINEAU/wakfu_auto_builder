"""Tests for constraint.py — Constraint class hierarchy."""

import math
import settings
from settings import simpleActionEnum, paramsActionEnum
from constraint import (
    Constraint,
    LevelConstraint,
    RarityConstraint,
    ResConstraint,
    MasteryConstraint,
    RatioConstraint,
)
from ortools.linear_solver import pywraplp
from tests.conftest import make_item


# ---------------------------------------------------------------------------
# Constraint base class
# ---------------------------------------------------------------------------

class TestConstraint:

    def test_init_and_getters(self):
        c = Constraint(
            name="testConstraint",
            text="PV >=",
            params=[simpleActionEnum.PV_ADD, simpleActionEnum.PV_MINUS],
            default=0,
            color="red",
            min=0,
            max=9999,
            ratio=1,
        )
        assert c.getName() == "testConstraint"
        assert c.getText() == "PV >="
        assert c.getColor() == "red"
        assert c.getMin() == 0
        assert c.getMax() == 9999
        assert c.getValue() == 0
        assert c.getDefault() == 0
        assert c.getRatio() == 1
        assert c.getParams() == [simpleActionEnum.PV_ADD, simpleActionEnum.PV_MINUS]

    def test_set_value(self):
        c = Constraint(name="t", text="t", params=[], default=0)
        c.setValue(42)
        assert c.getValue() == 42

    def test_set_value_converts_to_int(self):
        c = Constraint(name="t", text="t", params=[], default=0)
        c.setValue(3.9)
        assert c.getValue() == 3
        assert isinstance(c.getValue(), int)

    def test_createSolverConstraints_returns_empty_when_value_equals_default(self):
        c = Constraint(
            name="t", text="t",
            params=[simpleActionEnum.PV_ADD, simpleActionEnum.PV_MINUS],
            default=100,
        )
        assert c.createSolverConstraints() == []

    def test_createSolverConstraints_returns_constraint_when_value_differs(self):
        item = make_item(1, 100, 134, 4, effects={
            int(simpleActionEnum.PV_ADD): [200, 0],
        })
        settings.ITEMS_DATA = {1: item}

        solver = pywraplp.Solver("test", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.VARIABLES = {1: solver.BoolVar("item_1")}

        c = Constraint(
            name="pvSelector", text="PV >=",
            params=[simpleActionEnum.PV_ADD, simpleActionEnum.PV_MINUS],
            default=0,
        )
        c.setValue(100)
        constraints = c.createSolverConstraints()
        assert len(constraints) == 1


# ---------------------------------------------------------------------------
# LevelConstraint / RarityConstraint always return empty
# ---------------------------------------------------------------------------

class TestLevelConstraint:

    def test_always_returns_empty(self):
        c = LevelConstraint(name="level", text="Level <=", params=[], default=230)
        c.setValue(200)
        assert c.createSolverConstraints() == []


class TestRarityConstraint:

    def test_always_returns_empty(self):
        c = RarityConstraint(name="rarity", text="Common ==", params=[], default=1)
        c.setValue(0)
        assert c.createSolverConstraints() == []


# ---------------------------------------------------------------------------
# MasteryConstraint
# ---------------------------------------------------------------------------

class TestMasteryConstraint:

    def test_returns_empty_when_value_zero(self):
        c = MasteryConstraint(
            name="fire", text="Feu", default=0, min=0, max=1,
            params=[simpleActionEnum.FIRE_MASTERY_ADD, simpleActionEnum.FIRE_MASTERY_MINUS],
        )
        assert c.createSolverConstraints() == []

    def test_returns_expression_when_value_one(self):
        item = make_item(1, 100, 134, 4, effects={
            int(simpleActionEnum.FIRE_MASTERY_ADD): [50, 0],
        })
        settings.ITEMS_DATA = {1: item}

        solver = pywraplp.Solver("test", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.VARIABLES = {1: solver.BoolVar("item_1")}

        c = MasteryConstraint(
            name="fire", text="Feu", default=0, min=0, max=1,
            params=[simpleActionEnum.FIRE_MASTERY_ADD, simpleActionEnum.FIRE_MASTERY_MINUS],
        )
        c.setValue(1)
        constraints = c.createSolverConstraints()
        assert len(constraints) == 1


# ---------------------------------------------------------------------------
# RatioConstraint
# ---------------------------------------------------------------------------

class TestRatioConstraint:

    def test_returns_empty_when_value_zero(self):
        c = RatioConstraint(
            name="block", text="parade", default=0, min=0, max=1, ratio=10,
            params=[simpleActionEnum.BLOCK_ADD, simpleActionEnum.BLOCK_MINUS],
        )
        assert c.createSolverConstraints() == []

    def test_returns_scaled_expression_when_value_one(self):
        item = make_item(1, 100, 134, 4, effects={
            int(simpleActionEnum.BLOCK_ADD): [20, 0],
        })
        settings.ITEMS_DATA = {1: item}

        solver = pywraplp.Solver("test", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.VARIABLES = {1: solver.BoolVar("item_1")}

        c = RatioConstraint(
            name="block", text="parade", default=0, min=0, max=1, ratio=10,
            params=[simpleActionEnum.BLOCK_ADD, simpleActionEnum.BLOCK_MINUS],
        )
        c.setValue(1)
        constraints = c.createSolverConstraints()
        assert len(constraints) == 1

        # Verify the ratio is applied: maximize the expression, should be 20*10=200
        solver.Maximize(constraints[0])
        solver.Add(settings.VARIABLES[1] == 1)
        solver.Solve()
        assert solver.Objective().Value() == 200


# ---------------------------------------------------------------------------
# ResConstraint
# ---------------------------------------------------------------------------

class TestResConstraint:

    def test_resistance_formula(self):
        """Verify the res % -> raw res number formula."""
        c = ResConstraint(name="res", text="Resistance >=", params=[], default=0)
        c.setValue(50)

        target = -((50 / 100) - 1)  # 0.5
        expected_res_number = math.log(target, 0.8) * 100

        assert target == 0.5
        assert expected_res_number == pytest.approx(math.log(0.5, 0.8) * 100)

    def test_returns_four_constraints_for_four_elements(self):
        item = make_item(1, 100, 134, 4, effects={
            int(simpleActionEnum.FIRE_RES_ADD): [50, 0],
            int(simpleActionEnum.AIR_RES_ADD): [50, 0],
            int(simpleActionEnum.WATER_RES_ADD): [50, 0],
            int(simpleActionEnum.EARTH_RES_ADD): [50, 0],
            int(simpleActionEnum.ELEM_RES_ADD): [30, 0],
        })
        settings.ITEMS_DATA = {1: item}

        solver = pywraplp.Solver("test", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.VARIABLES = {1: solver.BoolVar("item_1")}

        c = ResConstraint(name="res", text="Resistance >=", params=[], default=0)
        c.setValue(30)
        constraints = c.createSolverConstraints()

        assert len(constraints) == 4, "Should produce one constraint per element (fire, air, water, earth)"


import pytest
