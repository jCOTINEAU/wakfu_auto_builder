# This Python file uses the following encoding: utf-8

from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot,QObject,Signal

import settings
from settings import eqTypeEnum
from settings import rarityEnum
from settings import simpleActionEnum
from settings import paramsActionEnum
from solver import createConstraintWithFunc,getEquipmentType,getRarity,getWaeponType,createSimpleAddSubstractConstraint,createParamsConstraint,createLevelConstraint
from ortools.linear_solver import pywraplp


QML_IMPORT_NAME = "wakfuConstraintSelector"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class WakfuConstraintSelector(QObject):

    def setCompleteConstraints(self):
        # number of item constraint
        self.completeConstraints.append(sum(var for var in settings.VARIABLES.values()) <= 14)

        #slot constraint
        self.completeConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.HEAD) <=1)
        self.completeConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.RING) <= 2)
        self.completeConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.LEGS) <= 1)
        self.completeConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.NECK) <= 1)
        self.completeConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.BACK) <= 1)
        self.completeConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.BELT) <= 1)
        self.completeConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.CHEST) <= 1)
        self.completeConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.SHOULDERS) <= 1)
        self.completeConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.EMBLEMA) <= 1)
        self.completeConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.PET) <= 1)
        self.completeConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.MOUNT) <= 1)

    #    #Epic / relic constraint
        self.completeConstraints.append(createConstraintWithFunc(getRarity,rarityEnum.EPIC) <=1)
        self.completeConstraints.append(createConstraintWithFunc(getRarity,rarityEnum.RELIC) <=1)

    #    #waepon constraint
        self.completeConstraints.append(createConstraintWithFunc(getWaeponType,"isPrimary") <=1)
        self.completeConstraints.append(createConstraintWithFunc(getWaeponType,"isSecondary") <=1)
        self.completeConstraints.append(createConstraintWithFunc(getWaeponType,"isTwoHanded") <=1)

        #at least one waepon
        self.completeConstraints.append(createConstraintWithFunc(getWaeponType,"isPrimary")+
            createConstraintWithFunc(getWaeponType,"isSecondary") +
            createConstraintWithFunc(getWaeponType,"isTwoHanded") >=1)

        #Exclusive between twoHanded and primary
        self.completeConstraints.append(createConstraintWithFunc(getWaeponType,"isPrimary")+
            createConstraintWithFunc(getWaeponType,"isTwoHanded") <=1)

        #Exclusive between twoHanded and secondary
        self.completeConstraints.append(createConstraintWithFunc(getWaeponType,"isSecondary")+
            createConstraintWithFunc(getWaeponType,"isTwoHanded") <=1)
#        #end waepon constraint

# SAD : cannot remove constraint, so impossible to do precomputation here
    def setPartialSimpleAddSubstractConstraints(self):
        partialConstraintEnum = {
            'pvSelector': [simpleActionEnum.PV_ADD,simpleActionEnum.PV_MINUS],
            'paSelector': [simpleActionEnum.PA_ADD,simpleActionEnum.PA_MINUS],
            'pmSelector': [simpleActionEnum.PM_ADD,simpleActionEnum.PM_MINUS],
            'pwSelector': [simpleActionEnum.PW_ADD,simpleActionEnum.PW_MINUS],
            'pcSelector': [simpleActionEnum.PC_ADD,simpleActionEnum.PC_MINUS],
            'iniSelector': [simpleActionEnum.INI_ADD,simpleActionEnum.INI_MINUS],
            'ccSelector': [simpleActionEnum.CC_ADD,simpleActionEnum.CC_MINUS],
            'dodgeSelector': [simpleActionEnum.DODGE_ADD,simpleActionEnum.DODGE_MINUS],
            'wisdomSelector': [simpleActionEnum.WIS_ADD,simpleActionEnum.WIS_MINUS],
            'ppSelector': [simpleActionEnum.PP_ADD,simpleActionEnum.PP_MINUS],
            'willSelector': [simpleActionEnum.WILL_ADD,simpleActionEnum.WILL_MINUS],
            'blockSelector': [simpleActionEnum.BLOCK_ADD,simpleActionEnum.BLOCK_MINUS],
            'lockSelector': [simpleActionEnum.LOCK_ADD,simpleActionEnum.LOCK_MINUS],
        }

        for key,value in partialConstraintEnum.items():
            constraint = createSimpleAddSubstractConstraint(value[0],value[1])
            self.partialSimpleAddSubstractConstraints[key]=constraint

    def setConstraints(self):
        self.solver.Add(createLevelConstraint(self.constraintValueFromUi.get('levelSelector',230)) == 0)

    def initSolver(self):

        self.completeConstraints = []
        self.mazimize = None
        self.partialSimpleAddSubstractConstraints = {}
        self.solver = pywraplp.Solver('Find optimal stuff based on constraints', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

        settings.VARIABLES={}

        rarity = [
         rarityEnum.WHITE if self.constraintValueFromUi.get('rarityCommonSelector',0) == 1 else -1,
         rarityEnum.GREEN if self.constraintValueFromUi.get('rarityRareSelector',0) == 1 else -1,
         rarityEnum.ORANGE if self.constraintValueFromUi.get('rarityMythicalSelector',0) == 1 else -1,
         rarityEnum.LEGENDARY if self.constraintValueFromUi.get('rarityLengendarySelector',0) == 1 else -1,
         rarityEnum.BLUE if self.constraintValueFromUi.get('rarityMemorySelector',0) == 1 else -1,
         rarityEnum.EPIC if self.constraintValueFromUi.get('rarityEpicSelector',0) == 1 else -1,
         rarityEnum.RELIC if self.constraintValueFromUi.get('rarityRelicSelector',0) == 1 else -1,
        ]

        for key,item in settings.ITEMS_DATA.items():
           # remove shards from item list so far
           if item['definition']['item'].get('shardsParameters',0) != 0:
               continue
           if item['definition']['item']['level'] >= self.constraintValueFromUi.get('levelSelector',230) :
               continue

           if item['definition']['item']['baseParameters']['rarity'] not in rarity:
               continue

           settings.VARIABLES[key]=self.solver.BoolVar(item['title']['fr']+str(item['definition']['item']['id']))


        self.setCompleteConstraints()
        self.setPartialSimpleAddSubstractConstraints()
        self.setConstraints()

        for constraint in self.completeConstraints:
            self.solver.Add(constraint)

        for key,constraint in self.partialSimpleAddSubstractConstraints.items():
            self.solver.Add(constraint >= self.constraintValueFromUi.get(key,0))

        self.solver.Maximize(createSimpleAddSubstractConstraint(simpleActionEnum.FIRE_MASTERY_ADD,simpleActionEnum.FIRE_MASTERY_MINUS)+
            createSimpleAddSubstractConstraint(simpleActionEnum.ELEM_MASTERY_ADD,simpleActionEnum.ELEM_MASTERY_MINUS)+
            createParamsConstraint(paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD,paramsActionEnum.RANDOM_NUMBER_MASTERY_MINUS)
            )


    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.constraintValueFromUi = {}


    @Slot(str,int, result=bool)
    def setConstraintValue(self,name,constraintValue):
        self.constraintValueFromUi[name]=constraintValue
        print(self.constraintValueFromUi[name])


    @Slot()
    def solve(self):

        self.initSolver()

        status = self.solver.Solve()

        myList = []

        # If an optimal solution has been found, print results
        if status == pywraplp.Solver.OPTIMAL:
          print('================= Solution =================')
          print(f'Solved in {self.solver.wall_time():.2f} milliseconds in {self.solver.iterations()} iterations')
          for key,variable in settings.VARIABLES.items():
              if variable.solution_value() == 1:
                  print(settings.ITEMS_DATA[key]['title']['fr'])
                  print(key)
                  myList.append({'id': key, 'name': settings.ITEMS_DATA[key]['title']['fr']})
        else:
          print('The solver could not find an optimal solution.')

        settings.OPTIMIZED_ITEM_LIST = myList








