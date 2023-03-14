from ortools.linear_solver import pywraplp
import settings
from settings import eqTypeEnum
from settings import rarityEnum
from settings import simpleActionEnum
from settings import paramsActionEnum
from settings import waeponEnum

def safeget(dct, *keys):
    for key in keys:
        try:
            dct = dct[key]
        except KeyError:
            return None
    return dct

def getEquipEffectValue(dct,equipId,arg2=None):
    var = safeget(dct,"definition","equipEffects",equipId,"effect","definition","params")
    if var != None:
        return var[0]+var[1]*50
    return 0

def getEquipmentType(dct,equipmentTypeId,arg2=None):
    var = dct["definition"]["item"]["baseParameters"]["itemTypeId"]
    if var != None and var == equipmentTypeId:
        return 1
    return 0

def getWaeponType(dct,waeponTypeString,arg2=None):
    var = safeget(dct,"definition","item","baseParameters",waeponTypeString)
    if var != None:
        return 1
    return 0

def getRarity(dct,rarity,arg2=None):
    var = safeget(dct,"definition","item","baseParameters","rarity")
    if var != None and var == rarity:
        return 1
    return 0

def getEquipEffectValueWithParams(dct,equipId,ratio=1):
    var = safeget(dct,"definition","equipEffects",equipId,"effect","definition","params")
    if var != None:
        if ratio >= var[2]:
            return var[0] * var[2]
        else :
            return var[0]*ratio
    return 0

def getLevel(dct):
    var = safeget(dct,"definition","item","level")
    if var != None:
        return var
    return 0

def createSimpleAddSubstractConstraint(actionAdd,actionMinus):
    return (createConstraintWithFunc(getEquipEffectValue,actionAdd) - createConstraintWithFunc(getEquipEffectValue,actionMinus))

def createParamsConstraint(actionAdd,actionMinus,ratio=1):
    return (createConstraintWithFunc(getEquipEffectValueWithParams,actionAdd,ratio) - createConstraintWithFunc(getEquipEffectValueWithParams,actionMinus,ratio))

def createConstraintWithFunc(function,arg1,arg2=None):
    return sum(var*function(settings.ITEMS_DATA[id],arg1,arg2) for id,var in settings.VARIABLES.items() if function(settings.ITEMS_DATA[id],arg1,arg2) != 0)

def createLevelConstraint(level):
    return sum(var for id,var in settings.VARIABLES.items() if getLevel(settings.ITEMS_DATA[id]) >= level )
