"""Tests for constraint base_value integration with stat profiles."""

import os
import sys
import math
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import settings
from settings import simpleActionEnum, paramsActionEnum
from solver import createSimpleAddSubstractConstraint, createParamsConstraint
from constraint import Constraint, ResConstraint
from ortools.linear_solver import pywraplp
from tests.conftest import make_item
import stat_profile_manager
from stat_profile_manager import CONSTRAINT_STAT_MAP, DEFAULT_STATS, resistance_percent_to_raw


# ---------------------------------------------------------------------------
# Constraint.base_value
# ---------------------------------------------------------------------------

class TestConstraintBaseValue:

    def test_default_base_value_is_zero(self):
        c = Constraint("test", "Test >=", params=[simpleActionEnum.PV_ADD, simpleActionEnum.PV_MINUS])
        assert c.getBaseValue() == 0

    def test_set_base_value(self):
        c = Constraint("test", "Test >=", params=[simpleActionEnum.PV_ADD, simpleActionEnum.PV_MINUS])
        c.setBaseValue(42)
        assert c.getBaseValue() == 42

    def test_base_value_reduces_threshold(self):
        """With base PV=200, constraint PV>=500 should only require equipment PV>=300."""
        item = make_item(1, 100, 134, 4, effects={
            int(simpleActionEnum.PV_ADD): [300, 0],
        })
        items = {1: item}
        solver = pywraplp.Solver("test", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.ITEMS_DATA = items
        settings.VARIABLES = {1: solver.BoolVar("item_1")}

        c = Constraint("pvSelector", "PV >=", params=[simpleActionEnum.PV_ADD, simpleActionEnum.PV_MINUS], default=0)
        c.setValue(500)
        c.setBaseValue(200)

        constraints = c.createSolverConstraints()
        assert len(constraints) == 1
        for sc in constraints:
            solver.Add(sc)

        solver.Maximize(settings.VARIABLES[1])
        status = solver.Solve()
        assert status == pywraplp.Solver.OPTIMAL
        assert settings.VARIABLES[1].solution_value() == 1

    def test_base_value_makes_constraint_stricter_without(self):
        """Without base value, PV>=500 with equipment providing 300 should be infeasible."""
        item = make_item(1, 100, 134, 4, effects={
            int(simpleActionEnum.PV_ADD): [300, 0],
        })
        items = {1: item}
        solver = pywraplp.Solver("test", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.ITEMS_DATA = items
        settings.VARIABLES = {1: solver.BoolVar("item_1")}

        c = Constraint("pvSelector", "PV >=", params=[simpleActionEnum.PV_ADD, simpleActionEnum.PV_MINUS], default=0)
        c.setValue(500)
        # No base value (default 0)

        for sc in c.createSolverConstraints():
            solver.Add(sc)

        solver.Maximize(settings.VARIABLES[1])
        status = solver.Solve()
        # Infeasible: equipment provides 300 but needs 500
        assert status == pywraplp.Solver.INFEASIBLE

    def test_base_value_larger_than_threshold(self):
        """If base >= threshold, constraint is trivially satisfied."""
        item = make_item(1, 100, 134, 4, effects={
            int(simpleActionEnum.LOCK_ADD): [5, 0],
        })
        items = {1: item}
        solver = pywraplp.Solver("test", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.ITEMS_DATA = items
        settings.VARIABLES = {1: solver.BoolVar("item_1")}

        c = Constraint("lockSelector", "Tacle >=",
                        params=[simpleActionEnum.LOCK_ADD, simpleActionEnum.LOCK_MINUS], default=0)
        c.setValue(20)
        c.setBaseValue(50)  # base (50) > threshold (20)

        for sc in c.createSolverConstraints():
            solver.Add(sc)

        # The item should be selectable even with 0 equipment contribution
        solver.Add(settings.VARIABLES[1] == 0)
        status = solver.Solve()
        assert status == pywraplp.Solver.OPTIMAL

    def test_skipped_when_value_equals_default(self):
        """Constraint is skipped when value == default, regardless of base_value."""
        c = Constraint("test", "Test >=", params=[simpleActionEnum.PV_ADD, simpleActionEnum.PV_MINUS], default=0)
        c.setValue(0)
        c.setBaseValue(100)
        assert c.createSolverConstraints() == []


# ---------------------------------------------------------------------------
# ResConstraint.base_value
# ---------------------------------------------------------------------------

class TestResConstraintBaseValue:

    def test_res_base_value_makes_feasible(self):
        """25% resist needs ~129 raw res per element.
        Equipment gives 100 per element = 100, which is short.
        Adding 30 raw base resistance → 130 >= 129, making it feasible."""
        item = make_item(1, 100, 134, 4, effects={
            int(simpleActionEnum.FIRE_RES_ADD): [100, 0],
            int(simpleActionEnum.AIR_RES_ADD): [100, 0],
            int(simpleActionEnum.WATER_RES_ADD): [100, 0],
            int(simpleActionEnum.EARTH_RES_ADD): [100, 0],
        })
        items = {1: item}
        solver = pywraplp.Solver("test", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.ITEMS_DATA = items
        settings.VARIABLES = {1: solver.BoolVar("item_1")}

        rc = ResConstraint("resConstraint", "Resistance >=", params=[], default=0)
        rc.setValue(25)
        rc.setBaseValue(30)  # 30 raw resistance from stat profile

        for sc in rc.createSolverConstraints():
            solver.Add(sc)

        solver.Maximize(settings.VARIABLES[1])
        status = solver.Solve()
        assert status == pywraplp.Solver.OPTIMAL
        assert settings.VARIABLES[1].solution_value() == 1

    def test_res_without_base_is_infeasible(self):
        """Same setup but without base resistance → infeasible (100 < 129)."""
        item = make_item(1, 100, 134, 4, effects={
            int(simpleActionEnum.FIRE_RES_ADD): [100, 0],
            int(simpleActionEnum.AIR_RES_ADD): [100, 0],
            int(simpleActionEnum.WATER_RES_ADD): [100, 0],
            int(simpleActionEnum.EARTH_RES_ADD): [100, 0],
        })
        items = {1: item}
        solver = pywraplp.Solver("test", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.ITEMS_DATA = items
        settings.VARIABLES = {1: solver.BoolVar("item_1")}

        rc = ResConstraint("resConstraint", "Resistance >=", params=[], default=0)
        rc.setValue(25)
        # No base value

        for sc in rc.createSolverConstraints():
            solver.Add(sc)

        solver.Maximize(settings.VARIABLES[1])
        status = solver.Solve()
        assert status == pywraplp.Solver.INFEASIBLE


# ---------------------------------------------------------------------------
# CONSTRAINT_STAT_MAP completeness
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# resistance_percent_to_raw
# ---------------------------------------------------------------------------

class TestResistancePercentToRaw:

    def test_zero_percent_returns_zero(self):
        assert resistance_percent_to_raw(0) == 0

    def test_negative_percent_returns_zero(self):
        assert resistance_percent_to_raw(-10) == 0

    def test_100_percent_returns_cap(self):
        assert resistance_percent_to_raw(100) == 99999

    def test_known_value_50_percent(self):
        expected = math.log(0.5, 0.8) * 100
        assert resistance_percent_to_raw(50) == pytest.approx(expected)

    def test_known_value_25_percent(self):
        expected = math.log(0.75, 0.8) * 100
        assert resistance_percent_to_raw(25) == pytest.approx(expected)

    def test_inverse_of_constraint_formula(self):
        """The conversion should use the same formula as ResConstraint."""
        pct = 40
        target = -((pct / 100) - 1)
        expected = math.log(target, 0.8) * 100
        assert resistance_percent_to_raw(pct) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# CONSTRAINT_STAT_MAP completeness
# ---------------------------------------------------------------------------

class TestConstraintStatMap:

    def test_all_stat_keys_exist_in_default_stats(self):
        """Every value in CONSTRAINT_STAT_MAP should be a key in DEFAULT_STATS."""
        for constraint_name, stat_key in CONSTRAINT_STAT_MAP.items():
            assert stat_key in DEFAULT_STATS, \
                f"CONSTRAINT_STAT_MAP[{constraint_name!r}] = {stat_key!r} not found in DEFAULT_STATS"

    def test_map_covers_all_simple_constraints(self):
        """All simple constraint selectors should be in the map."""
        expected = [
            "pvSelector", "paSelector", "pmSelector", "pwSelector",
            "pcSelector", "poSelector", "iniSelector", "ccSelector",
            "wisdomSelector", "ppSelector", "willSelector",
            "blockSelector", "lockSelector", "dodgeSelector",
            "resConstraint",
        ]
        for name in expected:
            assert name in CONSTRAINT_STAT_MAP, f"{name!r} missing from CONSTRAINT_STAT_MAP"

    def test_default_stats_key_count(self):
        """DEFAULT_STATS should have exactly the supported stat keys (15 constraint + 7 mastery)."""
        assert len(DEFAULT_STATS) == 22
