# This Python file uses the following encoding: utf-8
import os
import json
import settings
from paths import resource_path

def parse():

    data_dir = resource_path("data", settings.DATA_VERSION)

    itemPropertiesFile = open(os.path.join(data_dir, "itemProperties.json"), encoding="utf-8")
    itemPropertiesData = json.load(itemPropertiesFile)

    itemsFile = open(os.path.join(data_dir, "items.json"), encoding="utf-8")
    itemsData = json.load(itemsFile)

    equipmentItemTypesFile = open(os.path.join(data_dir, "equipmentItemTypes.json"), encoding="utf-8")
    equipmentItemTypesData = json.load(equipmentItemTypesFile)

    actionFile = open(os.path.join(data_dir, "actions.json"), encoding="utf-8")
    actionData = json.load(actionFile)

    settings.ITEMS_DATA=itemsData
    settings.EQUIPMENT_ITEM_TYPES_DATA=equipmentItemTypesData
    settings.ITEM_PROPERTIES_DATA=itemPropertiesData
    settings.ACTION_DATA=actionData

def restruct_item_into_id_map():

    resDict={}

    for item in settings.ITEMS_DATA:

        equipEffectsDict={}

        for equipEffect in item['definition']['equipEffects']:

            equipEffectsDict[equipEffect['effect']['definition']['actionId']]=equipEffect

        item['definition']['equipEffects']=equipEffectsDict

        resDict[item['definition']['item']['id']]=item

    settings.ITEMS_DATA=resDict

    resDict = {}

    for item in settings.EQUIPMENT_ITEM_TYPES_DATA:
        resDict[item['definition']['id']]=item

    settings.EQUIPMENT_ITEM_TYPES_DATA=resDict

    resDict = {}

    for action in settings.ACTION_DATA:
        resDict[action['definition']['id']]=action

    settings.ACTION_DATA=resDict


def _leaf_equip_positions(item):
    """Return (positions, disabled_positions) of the item's leaf equipment
    type. Handles both the 1.90- schema (info was inherited via parentId)
    and the 1.92+ schema (parentId dropped, leaf carries the info directly).
    """
    type_id = item['definition']['item']['baseParameters'].get('itemTypeId')
    entry = settings.EQUIPMENT_ITEM_TYPES_DATA.get(type_id)
    if entry is None:
        return [], []
    definition = entry['definition']
    positions = definition.get('equipmentPositions', [])
    disabled = definition.get('equipmentDisabledPositions', [])
    return positions, disabled


def isPrimaryWeapon(item):
    positions, disabled = _leaf_equip_positions(item)
    return 'FIRST_WEAPON' in positions and 'SECOND_WEAPON' not in disabled


def isSecondaryWeapon(item):
    positions, _ = _leaf_equip_positions(item)
    return 'SECOND_WEAPON' in positions


def isTwoHanded(item):
    positions, disabled = _leaf_equip_positions(item)
    return 'FIRST_WEAPON' in positions and 'SECOND_WEAPON' in disabled


def add_direct_weapon_type():

    for key,item in settings.ITEMS_DATA.items():
        if isPrimaryWeapon(item):
            settings.ITEMS_DATA[key]['definition']['item']['baseParameters']['isPrimary'] = 1
        if isSecondaryWeapon(item):
            settings.ITEMS_DATA[key]['definition']['item']['baseParameters']['isSecondary'] = 1
        if isTwoHanded(item):
            settings.ITEMS_DATA[key]['definition']['item']['baseParameters']['isTwoHanded'] = 1


def load_item_pairings():
    """Load all-or-none item groups from data_overrides/item_pairings.json.

    Groups referencing item IDs not present in ITEMS_DATA (e.g. after a
    Wakfu data-version bump) are dropped with a warning so the solver
    stays feasible.
    """
    path = resource_path("data_overrides", "item_pairings.json")
    if not os.path.exists(path):
        settings.ITEM_PAIRINGS = []
        return
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    kept = []
    for group in raw.get("groups", []):
        ids = group.get("items", [])
        missing = [i for i in ids if i not in settings.ITEMS_DATA]
        if missing:
            print(f"[pairings] dropping group {group.get('name', '?')!r}: "
                  f"item IDs not in current data: {missing}")
            continue
        kept.append({"name": group.get("name", ""), "items": list(ids)})
    settings.ITEM_PAIRINGS = kept


def setupJson():
    parse()
    restruct_item_into_id_map()
    add_direct_weapon_type()
    load_item_pairings()


# Display order for the optimized item list. Any slot not listed here
# (COSTUME, ACCESSORY, unknown) is placed at the end.
SLOT_ORDER = [
    "HEAD",
    "BACK",
    "SHOULDERS",
    "RING",
    "MOUNT",
    "PET",
    "EMBLEM",
    "FIRST_WEAPON_1H",
    "FIRST_WEAPON_2H",
    "SECOND_WEAPON",
    "LEGS",
    "BELT",
    "CHEST",
    "NECK",
]

SLOT_LABELS_FR = {
    "HEAD":            "Casque",
    "BACK":            "Cape",
    "SHOULDERS":       "Épaulettes",
    "RING":            "Anneau",
    "MOUNT":           "Monture",
    "PET":             "Familier",
    "EMBLEM":          "Emblème",
    "FIRST_WEAPON_1H": "Arme 1M",
    "FIRST_WEAPON_2H": "Arme 2M",
    "SECOND_WEAPON":   "Seconde main",
    "LEGS":            "Bottes",
    "BELT":            "Ceinture",
    "CHEST":           "Torse",
    "NECK":            "Amulette",
}

_SLOT_BY_TYPE_ID = {
    103: "RING",
    119: "LEGS",
    120: "NECK",
    132: "BACK",
    133: "BELT",
    134: "HEAD",
    136: "CHEST",
    138: "SHOULDERS",
    582: "PET",
    611: "MOUNT",
    646: "EMBLEM",
    849: "PET",             # Porte-bonheur (1.92+) — shares the PET slot in-game
}

def slot_of(item_id):
    """Return the logical slot key for an item id (see SLOT_ORDER).

    Direct lookup by itemTypeId first (rings, armor pieces, pet, mount…).
    For weapons — types that share FIRST_WEAPON / SECOND_WEAPON positions
    — we distinguish 1H / 2H / off-hand from equipmentPositions +
    equipmentDisabledPositions of the leaf type. This works for both the
    pre-1.92 schema (had parentId) and the 1.92+ schema (parentId dropped,
    leaf carries the discriminator directly).

    Falls back to "OTHER" for slots not in SLOT_ORDER (costume, accessory,
    unknown ids from stale saved builds).
    """
    item = settings.ITEMS_DATA.get(item_id)
    if item is None:
        return "OTHER"
    type_id = item["definition"]["item"]["baseParameters"]["itemTypeId"]
    direct = _SLOT_BY_TYPE_ID.get(type_id)
    if direct is not None:
        return direct
    positions, disabled = _leaf_equip_positions(item)
    if 'FIRST_WEAPON' in positions:
        return "FIRST_WEAPON_2H" if 'SECOND_WEAPON' in disabled else "FIRST_WEAPON_1H"
    if 'SECOND_WEAPON' in positions:
        return "SECOND_WEAPON"
    return "OTHER"


def gfx_id_of(item_id):
    """Return the Wakfu CDN gfxId for an item, or None if unknown."""
    item = settings.ITEMS_DATA.get(item_id)
    if item is None:
        return None
    return item["definition"]["item"]["graphicParameters"].get("gfxId")


def rarity_of(item_id):
    """Return the rarity int for an item (see settings.rarityEnum), or 0 if unknown."""
    item = settings.ITEMS_DATA.get(item_id)
    if item is None:
        return 0
    return item["definition"]["item"]["baseParameters"].get("rarity", 0)


def compute_stat_summary(item_ids):
    """Aggregate equip effects across `item_ids` into a list of stat rows.

    Each row: {'effect': <human string>, 'effectId': <int>, 'value': <int>}.
    Missing item IDs (stale saved build after a data bump) are skipped.
    """
    # Local imports keep wakutils importable without dragging solver.py at
    # module load time (used by low-level test helpers too).
    from settings import simpleActionEnum, paramsActionEnum
    from solver import getEquipEffectValue, getEquipEffectValueWithParams

    rows = []

    for action in simpleActionEnum:
        value = 0
        for iid in item_ids:
            item = settings.ITEMS_DATA.get(iid)
            if item:
                value += getEquipEffectValue(item, action.value)
        if value != 0:
            desc = settings.ACTION_DATA.get(action.value, {})
            effect_text = desc.get("definition", {}).get("effect",
                                                         f"Action {action.value}")
            rows.append({
                "effect":   f"{effect_text} : {value}",
                "effectId": action.value,
                "value":    value,
            })

    for action in paramsActionEnum:
        value = 0
        nb_elem = 0
        for iid in item_ids:
            item = settings.ITEMS_DATA.get(iid)
            if item is None:
                continue
            temp = getEquipEffectValueWithParams(item, action.value)
            value += temp
            if temp != 0:
                nb_elem = item["definition"]["equipEffects"][action.value]["effect"]["definition"]["params"][2]
        if value != 0:
            desc = settings.ACTION_DATA.get(action.value, {})
            effect_text = desc.get("definition", {}).get("effect",
                                                         f"Action {action.value}")
            rows.append({
                "effect":   f"{effect_text} : {value} on {int(nb_elem)} element",
                "effectId": action.value,
                "value":    value,
            })

    return rows


def name_of(item_id, lang="fr"):
    """Return the localized display name for an item id."""
    item = settings.ITEMS_DATA.get(item_id)
    if item is None:
        return f"#{item_id}"
    return item["title"].get(lang, f"#{item_id}")
