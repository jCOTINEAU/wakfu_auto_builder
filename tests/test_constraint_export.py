"""Tests for constraint export/import on WakfuConstraintSelector."""

import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import settings
from constraint import Constraint, LevelConstraint, RarityConstraint, MasteryConstraint, RatioConstraint
from wakfuConstraintSelectorTemplate import WakfuConstraintSelectorTemplate


# We test the export/import logic without instantiating the full QML WakfuConstraintSelector,
# by replicating the same constraint structure and calling the same logic.


def _build_models():
    """Build the same constraint model structure as WakfuConstraintSelector.__init__."""
    simple = WakfuConstraintSelectorTemplate([
        LevelConstraint('levelSelector', 'Level <=', params=[], default=230, min=1, max=999),
        RarityConstraint('rarityCommonSelector', 'Common ==', params=[], default=1, min=0, max=1),
        Constraint('pvSelector', 'PV >=', color='red',
                   params=[settings.simpleActionEnum.PV_ADD, settings.simpleActionEnum.PV_MINUS]),
        Constraint('paSelector', 'PA >=', color='blue',
                   params=[settings.simpleActionEnum.PA_ADD, settings.simpleActionEnum.PA_MINUS]),
    ])
    mastery = WakfuConstraintSelectorTemplate([
        MasteryConstraint('fireSelector', 'Feu', default=0, min=0, max=1,
                          params=[settings.simpleActionEnum.FIRE_MASTERY_ADD,
                                  settings.simpleActionEnum.FIRE_MASTERY_MINUS]),
        MasteryConstraint('waterSelector', 'Eau', default=1, min=0, max=1,
                          params=[settings.simpleActionEnum.WATER_MASTERY_ADD,
                                  settings.simpleActionEnum.WATER_MASTERY_MINUS]),
    ])
    other = WakfuConstraintSelectorTemplate([
        RatioConstraint('blockMaximizeSelector', 'parade', default=0, min=0, max=1, ratio=10,
                        params=[settings.simpleActionEnum.BLOCK_ADD, settings.simpleActionEnum.BLOCK_MINUS]),
    ])
    return [simple, mastery, other]


def _export(models):
    """Replicate WakfuConstraintSelector.exportConstraints logic."""
    data = {}
    for model in models:
        for constraint in model.getConstraints():
            data[constraint.getName()] = constraint.getValue()
    return json.dumps(data)


def _import(models, json_str):
    """Replicate WakfuConstraintSelector.importConstraints logic."""
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return
    for model in models:
        for constraint in model.getConstraints():
            if constraint.getName() in data:
                constraint.setValue(data[constraint.getName()])


# ── Tests ──


class TestExportConstraints:
    def test_export_returns_valid_json(self):
        models = _build_models()
        result = _export(models)
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_export_includes_all_constraint_names(self):
        models = _build_models()
        data = json.loads(_export(models))
        expected_names = {
            "levelSelector", "rarityCommonSelector", "pvSelector", "paSelector",
            "fireSelector", "waterSelector", "blockMaximizeSelector",
        }
        assert set(data.keys()) == expected_names

    def test_export_captures_default_values(self):
        models = _build_models()
        data = json.loads(_export(models))
        assert data["levelSelector"] == 230
        assert data["rarityCommonSelector"] == 1
        assert data["pvSelector"] == 0
        assert data["fireSelector"] == 0
        assert data["waterSelector"] == 1

    def test_export_captures_modified_values(self):
        models = _build_models()
        models[0].getConstraints()[0].setValue(180)  # level
        models[0].getConstraints()[2].setValue(500)   # PV
        models[1].getConstraints()[0].setValue(1)     # fire mastery on
        data = json.loads(_export(models))
        assert data["levelSelector"] == 180
        assert data["pvSelector"] == 500
        assert data["fireSelector"] == 1


class TestImportConstraints:
    def test_import_restores_values(self):
        models = _build_models()
        snapshot = '{"levelSelector": 180, "pvSelector": 500, "fireSelector": 1}'
        _import(models, snapshot)
        assert models[0].getConstraints()[0].getValue() == 180
        assert models[0].getConstraints()[2].getValue() == 500
        assert models[1].getConstraints()[0].getValue() == 1

    def test_import_preserves_unmentioned_constraints(self):
        models = _build_models()
        models[0].getConstraints()[3].setValue(42)  # PA = 42
        _import(models, '{"levelSelector": 150}')
        assert models[0].getConstraints()[0].getValue() == 150
        assert models[0].getConstraints()[3].getValue() == 42  # unchanged

    def test_import_ignores_unknown_names(self):
        models = _build_models()
        before = json.loads(_export(models))
        _import(models, '{"unknownSelector": 999}')
        after = json.loads(_export(models))
        assert before == after

    def test_import_handles_invalid_json(self):
        models = _build_models()
        before = json.loads(_export(models))
        _import(models, "not valid json {{{")
        after = json.loads(_export(models))
        assert before == after

    def test_import_handles_empty_json(self):
        models = _build_models()
        before = json.loads(_export(models))
        _import(models, "{}")
        after = json.loads(_export(models))
        assert before == after


class TestRoundTrip:
    def test_export_then_import_restores_state(self):
        """Modify constraints, export, reset, import — values should match."""
        models = _build_models()
        models[0].getConstraints()[0].setValue(180)
        models[0].getConstraints()[2].setValue(600)
        models[1].getConstraints()[0].setValue(1)
        models[1].getConstraints()[1].setValue(0)
        models[2].getConstraints()[0].setValue(1)

        snapshot = _export(models)

        # Reset to defaults
        models2 = _build_models()
        _import(models2, snapshot)

        assert models2[0].getConstraints()[0].getValue() == 180
        assert models2[0].getConstraints()[2].getValue() == 600
        assert models2[1].getConstraints()[0].getValue() == 1
        assert models2[1].getConstraints()[1].getValue() == 0
        assert models2[2].getConstraints()[0].getValue() == 1

    def test_save_and_load_build_with_constraints(self, tmp_path):
        """Full integration: export constraints, save build, load build, import constraints."""
        import build_manager

        models = _build_models()
        models[0].getConstraints()[0].setValue(200)
        models[0].getConstraints()[2].setValue(300)
        models[1].getConstraints()[0].setValue(1)

        constraints = json.loads(_export(models))
        items = [{"id": 1, "name": "Casque A"}]

        save_path = str(tmp_path / "builds.json")
        entry = build_manager.save_build("Test Build", items, constraints=constraints, path=save_path)

        loaded = build_manager.get_build(entry["id"], path=save_path)
        assert loaded["constraints"]["levelSelector"] == 200
        assert loaded["constraints"]["pvSelector"] == 300
        assert loaded["constraints"]["fireSelector"] == 1

        models2 = _build_models()
        _import(models2, json.dumps(loaded["constraints"]))
        assert models2[0].getConstraints()[0].getValue() == 200
        assert models2[0].getConstraints()[2].getValue() == 300
        assert models2[1].getConstraints()[0].getValue() == 1
