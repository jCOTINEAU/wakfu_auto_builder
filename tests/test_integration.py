"""Integration tests — full solve pipeline on real game data."""

import settings
from ortools.linear_solver import pywraplp
from ortools.linear_solver.pywraplp import SumArray
from settings import eqTypeEnum, rarityEnum, simpleActionEnum, paramsActionEnum
from solver import (
    createConstraintWithFunc,
    getEquipmentType,
    getRarity,
    getWaeponType,
    createSimpleAddSubstractConstraint,
    createParamsConstraint,
    getLevel,
)


class TestSolveWithMockData:
    """End-to-end solve using the minimal_equipment_set fixture."""

    def _run_solve(self, items_dict, level_cap=230, rarity_filter=None, pv_min=0, mastery_elems=None):
        """Helper: configure solver, add constraints, solve, return list of selected item IDs."""
        if rarity_filter is None:
            rarity_filter = [int(r) for r in rarityEnum]
        if mastery_elems is None:
            mastery_elems = []

        solver = pywraplp.Solver("test_solve", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.ITEMS_DATA = items_dict
        settings.VARIABLES = {}

        for key, item in items_dict.items():
            if item["definition"]["item"]["level"] > level_cap:
                continue
            if item["definition"]["item"]["baseParameters"]["rarity"] not in rarity_filter:
                continue
            settings.VARIABLES[key] = solver.BoolVar(
                item["title"]["fr"] + str(item["definition"]["item"]["id"])
            )

        stuff_constraints = []

        # max 14 items
        stuff_constraints.append(sum(var for var in settings.VARIABLES.values()) <= 14)

        # slot constraints
        stuff_constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.HEAD)) <= 1)
        stuff_constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.RING)) <= 2)
        stuff_constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.LEGS)) <= 1)
        stuff_constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.NECK)) <= 1)
        stuff_constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.BACK)) <= 1)
        stuff_constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.BELT)) <= 1)
        stuff_constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.CHEST)) <= 1)
        stuff_constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.SHOULDERS)) <= 1)
        stuff_constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.EMBLEMA)) <= 1)
        stuff_constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.PET)) <= 1)
        stuff_constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.MOUNT)) <= 1)

        # rarity constraints
        stuff_constraints.append(createConstraintWithFunc(getRarity, int(rarityEnum.EPIC)) <= 1)
        stuff_constraints.append(createConstraintWithFunc(getRarity, int(rarityEnum.RELIC)) <= 1)

        # weapon constraints
        stuff_constraints.append(createConstraintWithFunc(getWaeponType, "isPrimary") <= 1)
        stuff_constraints.append(createConstraintWithFunc(getWaeponType, "isSecondary") <= 1)
        stuff_constraints.append(createConstraintWithFunc(getWaeponType, "isTwoHanded") <= 1)
        stuff_constraints.append(
            createConstraintWithFunc(getWaeponType, "isPrimary")
            + createConstraintWithFunc(getWaeponType, "isSecondary")
            + createConstraintWithFunc(getWaeponType, "isTwoHanded") >= 1
        )
        stuff_constraints.append(
            createConstraintWithFunc(getWaeponType, "isPrimary")
            + createConstraintWithFunc(getWaeponType, "isTwoHanded") <= 1
        )
        stuff_constraints.append(
            createConstraintWithFunc(getWaeponType, "isSecondary")
            + createConstraintWithFunc(getWaeponType, "isTwoHanded") <= 1
        )

        for c in stuff_constraints:
            solver.Add(c)

        # PV minimum constraint
        if pv_min > 0:
            solver.Add(
                createSimpleAddSubstractConstraint(simpleActionEnum.PV_ADD, simpleActionEnum.PV_MINUS) >= pv_min
            )

        # Maximize mastery
        maximize = SumArray([])
        for action_add, action_minus in mastery_elems:
            maximize += createSimpleAddSubstractConstraint(action_add, action_minus)

        if mastery_elems:
            nb_elem = len(mastery_elems)
            maximize += createSimpleAddSubstractConstraint(
                simpleActionEnum.ELEM_MASTERY_ADD, simpleActionEnum.ELEM_MASTERY_MINUS, nb_elem
            )

        solver.Maximize(maximize)

        status = solver.Solve()
        selected = []
        if status == pywraplp.Solver.OPTIMAL:
            for key, variable in settings.VARIABLES.items():
                if variable.solution_value() == 1:
                    selected.append(key)

        return status, selected, solver

    def test_solve_finds_optimal(self, minimal_equipment_set):
        status, selected, solver = self._run_solve(
            minimal_equipment_set,
            mastery_elems=[(simpleActionEnum.FIRE_MASTERY_ADD, simpleActionEnum.FIRE_MASTERY_MINUS)],
        )
        assert status == pywraplp.Solver.OPTIMAL
        assert len(selected) > 0
        assert len(selected) <= 14

    def test_solve_respects_slot_constraints(self, minimal_equipment_set):
        status, selected, _ = self._run_solve(
            minimal_equipment_set,
            mastery_elems=[(simpleActionEnum.FIRE_MASTERY_ADD, simpleActionEnum.FIRE_MASTERY_MINUS)],
        )
        assert status == pywraplp.Solver.OPTIMAL

        selected_items = [minimal_equipment_set[k] for k in selected]

        type_counts = {}
        for item in selected_items:
            t = item["definition"]["item"]["baseParameters"]["itemTypeId"]
            type_counts[t] = type_counts.get(t, 0) + 1

        head_count = type_counts.get(int(eqTypeEnum.HEAD), 0)
        assert head_count <= 1, f"More than 1 head: {head_count}"

        ring_count = type_counts.get(int(eqTypeEnum.RING), 0)
        assert ring_count <= 2, f"More than 2 rings: {ring_count}"

    def test_solve_selects_weapon(self, minimal_equipment_set):
        status, selected, _ = self._run_solve(
            minimal_equipment_set,
            mastery_elems=[(simpleActionEnum.FIRE_MASTERY_ADD, simpleActionEnum.FIRE_MASTERY_MINUS)],
        )
        assert status == pywraplp.Solver.OPTIMAL

        has_weapon = False
        for k in selected:
            bp = minimal_equipment_set[k]["definition"]["item"]["baseParameters"]
            if bp.get("isPrimary") or bp.get("isSecondary") or bp.get("isTwoHanded"):
                has_weapon = True
        assert has_weapon, "Solver should select at least one weapon"

    def test_solve_maximizes_fire_mastery(self, minimal_equipment_set):
        status, selected, solver = self._run_solve(
            minimal_equipment_set,
            mastery_elems=[(simpleActionEnum.FIRE_MASTERY_ADD, simpleActionEnum.FIRE_MASTERY_MINUS)],
        )
        assert status == pywraplp.Solver.OPTIMAL
        assert solver.Objective().Value() > 0

        # Weapon (100 fire mastery) should be selected
        assert 2013 in selected, "Primary weapon with highest fire mastery should be selected"

    def test_pv_constraint_is_respected(self, minimal_equipment_set):
        status, selected, _ = self._run_solve(
            minimal_equipment_set,
            pv_min=200,
            mastery_elems=[(simpleActionEnum.FIRE_MASTERY_ADD, simpleActionEnum.FIRE_MASTERY_MINUS)],
        )
        assert status == pywraplp.Solver.OPTIMAL

        from solver import getEquipEffectValue
        total_pv = sum(
            getEquipEffectValue(minimal_equipment_set[k], int(simpleActionEnum.PV_ADD))
            for k in selected
        )
        assert total_pv >= 200, f"Total PV {total_pv} should be >= 200"


class TestSolveWithRealData:
    """End-to-end test using the actual game data JSON files."""

    def test_full_solve_with_real_data(self):
        from wakutils import setupJson

        setupJson()

        solver = pywraplp.Solver("real_data", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
        settings.VARIABLES = {}

        rarity_filter = [int(r) for r in rarityEnum]

        for key, item in settings.ITEMS_DATA.items():
            if item["definition"]["item"].get("shardsParameters", 0) != 0:
                continue
            if item["definition"]["item"]["level"] > 230:
                continue
            if item["definition"]["item"]["baseParameters"]["rarity"] not in rarity_filter:
                continue
            settings.VARIABLES[key] = solver.BoolVar(
                item["title"]["fr"] + str(item["definition"]["item"]["id"])
            )

        constraints = []
        constraints.append(sum(var for var in settings.VARIABLES.values()) <= 14)

        constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.HEAD)) <= 1)
        constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.RING)) <= 2)
        constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.LEGS)) <= 1)
        constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.NECK)) <= 1)
        constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.BACK)) <= 1)
        constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.BELT)) <= 1)
        constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.CHEST)) <= 1)
        constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.SHOULDERS)) <= 1)
        constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.EMBLEMA)) <= 1)
        constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.PET)) <= 1)
        constraints.append(createConstraintWithFunc(getEquipmentType, int(eqTypeEnum.MOUNT)) <= 1)

        constraints.append(createConstraintWithFunc(getRarity, int(rarityEnum.EPIC)) <= 1)
        constraints.append(createConstraintWithFunc(getRarity, int(rarityEnum.RELIC)) <= 1)

        constraints.append(createConstraintWithFunc(getWaeponType, "isPrimary") <= 1)
        constraints.append(createConstraintWithFunc(getWaeponType, "isSecondary") <= 1)
        constraints.append(createConstraintWithFunc(getWaeponType, "isTwoHanded") <= 1)
        constraints.append(
            createConstraintWithFunc(getWaeponType, "isPrimary")
            + createConstraintWithFunc(getWaeponType, "isSecondary")
            + createConstraintWithFunc(getWaeponType, "isTwoHanded") >= 1
        )
        constraints.append(
            createConstraintWithFunc(getWaeponType, "isPrimary")
            + createConstraintWithFunc(getWaeponType, "isTwoHanded") <= 1
        )
        constraints.append(
            createConstraintWithFunc(getWaeponType, "isSecondary")
            + createConstraintWithFunc(getWaeponType, "isTwoHanded") <= 1
        )

        for c in constraints:
            solver.Add(c)

        # Maximize fire + water mastery
        maximize = SumArray([])
        maximize += createSimpleAddSubstractConstraint(
            simpleActionEnum.FIRE_MASTERY_ADD, simpleActionEnum.FIRE_MASTERY_MINUS
        )
        maximize += createSimpleAddSubstractConstraint(
            simpleActionEnum.WATER_MASTERY_ADD, simpleActionEnum.WATER_MASTERY_MINUS
        )
        maximize += createSimpleAddSubstractConstraint(
            simpleActionEnum.ELEM_MASTERY_ADD, simpleActionEnum.ELEM_MASTERY_MINUS, 2
        )
        maximize += createParamsConstraint(
            paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD,
            paramsActionEnum.RANDOM_NUMBER_MASTERY_MINUS,
            2,
        )

        solver.Maximize(maximize)

        status = solver.Solve()
        assert status == pywraplp.Solver.OPTIMAL

        selected = []
        for key, variable in settings.VARIABLES.items():
            if variable.solution_value() == 1:
                selected.append(key)

        assert len(selected) > 0, "Solver should find at least one item"
        assert len(selected) <= 14, "Cannot select more than 14 items"
        assert solver.Objective().Value() > 0, "Objective (mastery) should be positive"
