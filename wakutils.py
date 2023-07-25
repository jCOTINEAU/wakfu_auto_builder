# This Python file uses the following encoding: utf-8
import json
import settings
import tempfile

def parse():

    itemPropertiesFile = open("data/1.78.1.7/itemProperties.json", encoding="utf-8")
    itemPropertiesData = json.load(itemPropertiesFile)

    itemsFile = open("data/1.78.1.7/items.json", encoding="utf-8")
    itemsData = json.load(itemsFile)

    equipmentItemTypesFile = open("data/1.78.1.7/equipmentItemTypes.json", encoding="utf-8")
    equipmentItemTypesData = json.load(equipmentItemTypesFile)

    actionFile = open("data/1.78.1.7/actions.json", encoding="utf-8")
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


def setupJson():
    parse()
    restruct_item_into_id_map()
    add_direct_weapon_type()

    json_object= json.dumps(settings.ACTION_DATA,indent=4)

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as outfile:
        outfile.write(json_object)
        # find a place to put the tempory files | outfile.name to get path


