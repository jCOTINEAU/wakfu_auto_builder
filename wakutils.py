# This Python file uses the following encoding: utf-8
import os
import json
import settings

def parse():

    current_dir = os.path.dirname(os.path.abspath(__file__))

    version = settings.DATA_VERSION
    data_dir = os.path.join(current_dir, "data", version)

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


def isPrimaryWeapon(item):

    try:
        equipmentType = settings.EQUIPMENT_ITEM_TYPES_DATA[settings.EQUIPMENT_ITEM_TYPES_DATA[item['definition']['item']['baseParameters']['itemTypeId']]['definition']['parentId']]
        return 'FIRST_WEAPON' in equipmentType['definition']['equipmentPositions'] and not 'SECOND_WEAPON' in equipmentType['definition']['equipmentDisabledPositions']
    #non weapon item have parent id 118 which does not exist
    except KeyError:
        return False


def isSecondaryWeapon(item):

    try:
        equipmentType = settings.EQUIPMENT_ITEM_TYPES_DATA[settings.EQUIPMENT_ITEM_TYPES_DATA[item['definition']['item']['baseParameters']['itemTypeId']]['definition']['parentId']]
        if 'SECOND_WEAPON' in equipmentType['definition']['equipmentPositions']:
            return True
    #non weapon item have parent id 118 which does not exist
    except KeyError:
        return False

def isTwoHanded(item):

    try:
        equipmentType = settings.EQUIPMENT_ITEM_TYPES_DATA[settings.EQUIPMENT_ITEM_TYPES_DATA[item['definition']['item']['baseParameters']['itemTypeId']]['definition']['parentId']]
        if 'FIRST_WEAPON' in equipmentType['definition']['equipmentPositions'] and 'SECOND_WEAPON' in equipmentType['definition']['equipmentDisabledPositions']:
            return True
        return False
    #non weapon item have parent id 118 which does not exist
    except KeyError:
        return False


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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_dir, "data_overrides", "item_pairings.json")
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
}

# Weapon typeIds share the FIRST_WEAPON / SECOND_WEAPON positions;
# distinguishing 1H / 2H / off-hand needs the parent type id.
_SLOT_BY_PARENT_ID = {
    518: "FIRST_WEAPON_1H",
    519: "FIRST_WEAPON_2H",
    520: "SECOND_WEAPON",
}


def slot_of(item_id):
    """Return the logical slot key for an item id (see SLOT_ORDER).

    Falls back to "OTHER" for items whose slot is not in SLOT_ORDER
    (costumes, accessories, or unknown ids from stale saved builds).
    """
    item = settings.ITEMS_DATA.get(item_id)
    if item is None:
        return "OTHER"
    type_id = item["definition"]["item"]["baseParameters"]["itemTypeId"]
    direct = _SLOT_BY_TYPE_ID.get(type_id)
    if direct is not None:
        return direct
    type_entry = settings.EQUIPMENT_ITEM_TYPES_DATA.get(type_id)
    if type_entry is None:
        return "OTHER"
    parent_id = type_entry["definition"].get("parentId")
    return _SLOT_BY_PARENT_ID.get(parent_id, "OTHER")


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


def name_of(item_id, lang="fr"):
    """Return the localized display name for an item id."""
    item = settings.ITEMS_DATA.get(item_id)
    if item is None:
        return f"#{item_id}"
    return item["title"].get(lang, f"#{item_id}")
