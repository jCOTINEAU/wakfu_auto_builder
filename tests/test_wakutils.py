"""Tests for wakutils.py — JSON parsing, restructuring, and weapon type tagging."""

import json
import os
import settings
from tests.conftest import make_raw_item


class TestParse:

    def test_parse_loads_all_json_files(self):
        from wakutils import parse

        parse()

        assert len(settings.ITEMS_DATA) > 0
        assert len(settings.EQUIPMENT_ITEM_TYPES_DATA) > 0
        assert len(settings.ITEM_PROPERTIES_DATA) > 0
        assert len(settings.ACTION_DATA) > 0

    def test_items_data_is_list_before_restructuring(self):
        from wakutils import parse

        parse()

        assert isinstance(settings.ITEMS_DATA, list)
        first_item = settings.ITEMS_DATA[0]
        assert "definition" in first_item
        assert isinstance(first_item["definition"]["equipEffects"], list)


class TestRestructItemIntoIdMap:

    def test_items_become_dict_keyed_by_id(self):
        settings.ITEMS_DATA = [
            make_raw_item(100, 50, 134, 4, effects={20: [10, 0]}, title="Item A"),
            make_raw_item(200, 80, 136, 2, effects={41: [5, 0]}, title="Item B"),
        ]
        settings.EQUIPMENT_ITEM_TYPES_DATA = []
        settings.ACTION_DATA = []

        from wakutils import restruct_item_into_id_map
        restruct_item_into_id_map()

        assert isinstance(settings.ITEMS_DATA, dict)
        assert 100 in settings.ITEMS_DATA
        assert 200 in settings.ITEMS_DATA

    def test_equip_effects_become_dict_keyed_by_action_id(self):
        settings.ITEMS_DATA = [
            make_raw_item(100, 50, 134, 4, effects={20: [10, 0], 122: [30, 0]}),
        ]
        settings.EQUIPMENT_ITEM_TYPES_DATA = []
        settings.ACTION_DATA = []

        from wakutils import restruct_item_into_id_map
        restruct_item_into_id_map()

        effects = settings.ITEMS_DATA[100]["definition"]["equipEffects"]
        assert isinstance(effects, dict)
        assert 20 in effects
        assert 122 in effects
        assert effects[20]["effect"]["definition"]["params"] == [10, 0]

    def test_equipment_types_become_dict_keyed_by_id(self):
        settings.ITEMS_DATA = []
        settings.EQUIPMENT_ITEM_TYPES_DATA = [
            {"definition": {"id": 134, "equipmentPositions": ["HEAD"]}},
            {"definition": {"id": 136, "equipmentPositions": ["CHEST"]}},
        ]
        settings.ACTION_DATA = []

        from wakutils import restruct_item_into_id_map
        restruct_item_into_id_map()

        assert isinstance(settings.EQUIPMENT_ITEM_TYPES_DATA, dict)
        assert 134 in settings.EQUIPMENT_ITEM_TYPES_DATA
        assert 136 in settings.EQUIPMENT_ITEM_TYPES_DATA

    def test_actions_become_dict_keyed_by_id(self):
        settings.ITEMS_DATA = []
        settings.EQUIPMENT_ITEM_TYPES_DATA = []
        settings.ACTION_DATA = [
            {"definition": {"id": 20, "effect": "PV"}},
            {"definition": {"id": 122, "effect": "Fire mastery"}},
        ]

        from wakutils import restruct_item_into_id_map
        restruct_item_into_id_map()

        assert isinstance(settings.ACTION_DATA, dict)
        assert 20 in settings.ACTION_DATA
        assert 122 in settings.ACTION_DATA


class TestSetupJsonFull:
    """Integration test: runs the full setupJson pipeline on real data files."""

    def test_setup_json_loads_and_restructures(self):
        from wakutils import setupJson

        setupJson()

        assert isinstance(settings.ITEMS_DATA, dict)
        assert len(settings.ITEMS_DATA) > 0

        some_item_id = next(iter(settings.ITEMS_DATA))
        item = settings.ITEMS_DATA[some_item_id]
        assert "definition" in item
        assert isinstance(item["definition"]["equipEffects"], dict)

    def test_weapon_types_are_tagged(self):
        from wakutils import setupJson

        setupJson()

        has_primary = False
        has_secondary = False
        has_two_handed = False
        for item in settings.ITEMS_DATA.values():
            bp = item["definition"]["item"]["baseParameters"]
            if bp.get("isPrimary"):
                has_primary = True
            if bp.get("isSecondary"):
                has_secondary = True
            if bp.get("isTwoHanded"):
                has_two_handed = True

        assert has_primary, "No primary weapon found after weapon tagging"
        assert has_two_handed, "No two-handed weapon found after weapon tagging"
