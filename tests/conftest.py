import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import settings


def make_item(item_id, level, item_type_id, rarity, effects=None, title="Test Item", weapon_flags=None):
    """Build a mock item dict matching the restructured format (equipEffects keyed by actionId)."""
    equip_effects = {}
    for action_id, params in (effects or {}).items():
        equip_effects[action_id] = {
            "effect": {
                "definition": {
                    "actionId": action_id,
                    "params": params,
                }
            }
        }

    base_params = {
        "itemTypeId": item_type_id,
        "rarity": rarity,
    }
    if weapon_flags:
        base_params.update(weapon_flags)

    return {
        "definition": {
            "item": {
                "id": item_id,
                "level": level,
                "baseParameters": base_params,
            },
            "equipEffects": equip_effects,
        },
        "title": {"fr": title},
    }


def make_raw_item(item_id, level, item_type_id, rarity, effects=None, title="Test Item"):
    """Build a mock item dict in the RAW JSON format (equipEffects as a list), before restructuring."""
    equip_effects_list = []
    for action_id, params in (effects or {}).items():
        equip_effects_list.append({
            "effect": {
                "definition": {
                    "actionId": action_id,
                    "params": params,
                }
            }
        })

    return {
        "definition": {
            "item": {
                "id": item_id,
                "level": level,
                "baseParameters": {
                    "itemTypeId": item_type_id,
                    "rarity": rarity,
                },
            },
            "equipEffects": equip_effects_list,
        },
        "title": {"fr": title},
    }


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset all settings globals before each test."""
    settings.initGlobal()
    yield
    settings.initGlobal()


@pytest.fixture
def sample_item():
    """A single HEAD item (level 200, legendary) with PV_ADD=100 and fire mastery=50."""
    return make_item(
        item_id=1001,
        level=200,
        item_type_id=int(settings.eqTypeEnum.HEAD),
        rarity=int(settings.rarityEnum.LEGENDARY),
        effects={
            int(settings.simpleActionEnum.PV_ADD): [100, 0],
            int(settings.simpleActionEnum.FIRE_MASTERY_ADD): [50, 0],
        },
        title="Casque Legendaire",
    )


@pytest.fixture
def sample_item_with_params():
    """An item with a params-based effect (RANDOM_NUMBER_MASTERY_ADD): 30 per element, 3 elements."""
    return make_item(
        item_id=1002,
        level=180,
        item_type_id=int(settings.eqTypeEnum.CHEST),
        rarity=int(settings.rarityEnum.EPIC),
        effects={
            int(settings.paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD): [30, 0, 3],
        },
        title="Plastron Epique",
    )


@pytest.fixture
def minimal_equipment_set():
    """A minimal set of 14 items covering all slots + weapon, suitable for a full solve."""
    from settings import eqTypeEnum, rarityEnum, simpleActionEnum

    head = make_item(2001, 200, int(eqTypeEnum.HEAD), int(rarityEnum.LEGENDARY),
                     {int(simpleActionEnum.PV_ADD): [80, 0], int(simpleActionEnum.FIRE_MASTERY_ADD): [40, 0]},
                     title="Casque A", weapon_flags={})
    chest = make_item(2002, 200, int(eqTypeEnum.CHEST), int(rarityEnum.LEGENDARY),
                      {int(simpleActionEnum.PV_ADD): [60, 0], int(simpleActionEnum.WATER_MASTERY_ADD): [35, 0]},
                      title="Plastron A")
    legs = make_item(2003, 200, int(eqTypeEnum.LEGS), int(rarityEnum.LEGENDARY),
                     {int(simpleActionEnum.PV_ADD): [50, 0]}, title="Jambieres A")
    shoulders = make_item(2004, 200, int(eqTypeEnum.SHOULDERS), int(rarityEnum.LEGENDARY),
                          {int(simpleActionEnum.PV_ADD): [40, 0]}, title="Epaulettes A")
    belt = make_item(2005, 200, int(eqTypeEnum.BELT), int(rarityEnum.LEGENDARY),
                     {int(simpleActionEnum.PV_ADD): [30, 0]}, title="Ceinture A")
    neck = make_item(2006, 200, int(eqTypeEnum.NECK), int(rarityEnum.LEGENDARY),
                     {int(simpleActionEnum.PV_ADD): [25, 0]}, title="Amulette A")
    ring1 = make_item(2007, 200, int(eqTypeEnum.RING), int(rarityEnum.LEGENDARY),
                      {int(simpleActionEnum.PV_ADD): [20, 0]}, title="Anneau A")
    ring2 = make_item(2008, 200, int(eqTypeEnum.RING), int(rarityEnum.GREEN),
                      {int(simpleActionEnum.PV_ADD): [15, 0]}, title="Anneau B")
    back = make_item(2009, 200, int(eqTypeEnum.BACK), int(rarityEnum.LEGENDARY),
                     {int(simpleActionEnum.PV_ADD): [20, 0]}, title="Cape A")
    pet = make_item(2010, 200, int(eqTypeEnum.PET), int(rarityEnum.LEGENDARY),
                    {int(simpleActionEnum.PV_ADD): [10, 0]}, title="Familier A")
    mount = make_item(2011, 200, int(eqTypeEnum.MOUNT), int(rarityEnum.LEGENDARY),
                      {int(simpleActionEnum.PV_ADD): [10, 0]}, title="Monture A")
    emblem = make_item(2012, 200, int(eqTypeEnum.EMBLEMA), int(rarityEnum.LEGENDARY),
                       {int(simpleActionEnum.PV_ADD): [10, 0]}, title="Embleme A")

    weapon_primary = make_item(2013, 200, 518, int(rarityEnum.LEGENDARY),
                               {int(simpleActionEnum.FIRE_MASTERY_ADD): [100, 0]},
                               title="Epee A", weapon_flags={"isPrimary": 1})
    weapon_secondary = make_item(2014, 200, 520, int(rarityEnum.GREEN),
                                 {int(simpleActionEnum.FIRE_MASTERY_ADD): [30, 0]},
                                 title="Bouclier A", weapon_flags={"isSecondary": 1})

    items = [head, chest, legs, shoulders, belt, neck, ring1, ring2,
             back, pet, mount, emblem, weapon_primary, weapon_secondary]

    return {item["definition"]["item"]["id"]: item for item in items}
