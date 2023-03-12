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

def solve():

    # Create the linear solver using the CBC backend
    solver = pywraplp.Solver('Find best Hat', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    for key,item in settings.ITEMS_DATA.items():
        settings.VARIABLES[key]=solver.BoolVar(item['title']['fr']+str(item['definition']['item']['id']))

    # number of item constraint
    solver.Add(sum(var for var in settings.VARIABLES.values()) <= 14)

    #slot constraint
    solver.Add(createConstraintWithFunc(getEquipmentType,eqTypeEnum.HEAD) ==1)
    solver.Add(createConstraintWithFunc(getEquipmentType,eqTypeEnum.RING) == 2)
    solver.Add(createConstraintWithFunc(getEquipmentType,eqTypeEnum.LEGS) == 1)
    solver.Add(createConstraintWithFunc(getEquipmentType,eqTypeEnum.NECK) == 1)
    solver.Add(createConstraintWithFunc(getEquipmentType,eqTypeEnum.BACK) == 1)
    solver.Add(createConstraintWithFunc(getEquipmentType,eqTypeEnum.BELT) == 1)
    solver.Add(createConstraintWithFunc(getEquipmentType,eqTypeEnum.CHEST) == 1)
    solver.Add(createConstraintWithFunc(getEquipmentType,eqTypeEnum.SHOULDERS) == 1)
    solver.Add(createConstraintWithFunc(getEquipmentType,eqTypeEnum.EMBLEMA) == 1)
    solver.Add(createConstraintWithFunc(getEquipmentType,eqTypeEnum.PET) == 1)
    solver.Add(createConstraintWithFunc(getEquipmentType,eqTypeEnum.MOUNT) == 1)

#    #Epic / relic constraint
    solver.Add(createConstraintWithFunc(getRarity,rarityEnum.EPIC) <=1)
    solver.Add(createConstraintWithFunc(getRarity,rarityEnum.RELIC) <=1)

#    #waepon constraint
    solver.Add(createConstraintWithFunc(getWaeponType,"isPrimary") <=1)
    solver.Add(createConstraintWithFunc(getWaeponType,"isSecondary") <=1)
    solver.Add(createConstraintWithFunc(getWaeponType,"isTwoHanded") <=1)

    #at least one waepon
    solver.Add(createConstraintWithFunc(getWaeponType,"isPrimary")+
        createConstraintWithFunc(getWaeponType,"isSecondary") +
        createConstraintWithFunc(getWaeponType,"isTwoHanded") >=1)

    #Exclusive between twoHanded and primary
    solver.Add(createConstraintWithFunc(getWaeponType,"isPrimary")+
        createConstraintWithFunc(getWaeponType,"isTwoHanded") <=1)

    #Exclusive between twoHanded and secondary
    solver.Add(createConstraintWithFunc(getWaeponType,"isSecondary")+
        createConstraintWithFunc(getWaeponType,"isTwoHanded") <=1)
    #end waepon constraint

    # add test pa constraint
    solver.Add(createSimpleAddSubstractConstraint(simpleActionEnum.PA_ADD,simpleActionEnum.PA_MINUS) >=5)
    solver.Add(createSimpleAddSubstractConstraint(simpleActionEnum.PM_ADD,simpleActionEnum.PM_MINUS) >=2)
    solver.Add(createSimpleAddSubstractConstraint(simpleActionEnum.PO_ADD,simpleActionEnum.PO_MINUS) >=0)
    solver.Add(createSimpleAddSubstractConstraint(simpleActionEnum.PC_ADD,simpleActionEnum.PC_ADD) >=0)
    solver.Add(createSimpleAddSubstractConstraint(simpleActionEnum.PW_ADD,simpleActionEnum.PW_MINUS) >=0)
    solver.Add(createSimpleAddSubstractConstraint(simpleActionEnum.INI_ADD,simpleActionEnum.INI_MINUS) >=0)


#    solver.Maximize(createSimpleAddSubstractConstraint(simpleActionEnum.HEALTH_ADD,simpleActionEnum.HEALTH_MINUS))
    solver.Maximize(createSimpleAddSubstractConstraint(simpleActionEnum.FIRE_MASTERY_ADD,simpleActionEnum.FIRE_MASTERY_MINUS)+
        createSimpleAddSubstractConstraint(simpleActionEnum.ELEM_MASTERY_ADD,simpleActionEnum.ELEM_MASTERY_MINUS)+
        createParamsConstraint(paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD,paramsActionEnum.RANDOM_NUMBER_MASTERY_MINUS)
        )


    status = solver.Solve()

    myList = []

    # If an optimal solution has been found, print results
    if status == pywraplp.Solver.OPTIMAL:
      print('================= Solution =================')
      print(f'Solved in {solver.wall_time():.2f} milliseconds in {solver.iterations()} iterations')
      for key,variable in settings.VARIABLES.items():
          if variable.solution_value() == 1:
              print(settings.ITEMS_DATA[key]['title']['fr'])
              print(key)
              myList.append({'id': key, 'name': settings.ITEMS_DATA[key]['title']['fr']})
    else:
      print('The solver could not find an optimal solution.')

    settings.OPTIMIZED_ITEM_LIST = myList

