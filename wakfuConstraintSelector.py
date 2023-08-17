# This Python file uses the following encoding: utf-8

from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot,QObject,Signal,QAbstractItemModel

import settings
from settings import eqTypeEnum
from settings import rarityEnum
from settings import simpleActionEnum
from settings import paramsActionEnum
from solver import createConstraintWithFunc,getEquipmentType,getRarity,getWaeponType,createSimpleAddSubstractConstraint,createParamsConstraint,createLevelConstraint
from ortools.linear_solver import pywraplp
from ortools.linear_solver.linear_solver_natural_api import SumArray
from wakfuConstraintSelectorTemplate import WakfuConstraintSelectorTemplate
from constraint import Constraint,ResConstraint,LevelConstraint,RarityConstraint,MasteryConstraint,RatioConstraint
import math


QML_IMPORT_NAME = "wakfuConstraintSelector"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class WakfuConstraintSelector(QObject):

    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.constraintValueFromUi = {}

        self.simpleConstraintModel = WakfuConstraintSelectorTemplate([
            LevelConstraint('levelSelector','Level <=',params=[],default=230,min=1,max=999),
            RarityConstraint('rarityCommonSelector','Common ==',params=[],default=1,min=0,max=1,color='white'),
            RarityConstraint('rarityRareSelector','Rare ==',params=[],default=1,min=0,max=1,color='green'),
            RarityConstraint('rarityMythicalSelector','Mythical ==',params=[],default=1,min=0,max=1,color='orange'),
            RarityConstraint('rarityLegendarySelector','Legendary ==',params=[],default=1,min=0,max=1,color='yellow'),
            RarityConstraint('rarityMemorySelector','Memory ==',params=[],default=1,min=0,max=1,color='lightblue'),
            RarityConstraint('rarityEpicSelector','Epic ==',params=[],default=1,min=0,max=1,color='purple'),
            RarityConstraint('rarityRelicSelector','Relic ==',params=[],default=1,min=0,max=1,color='pink'),
            Constraint('pvSelector','PV >=',color='red',params=[simpleActionEnum.PV_ADD,simpleActionEnum.PV_MINUS]),
            Constraint('paSelector','PA >=',color='blue',params=[simpleActionEnum.PA_ADD,simpleActionEnum.PA_MINUS]),
            Constraint('pmSelector','PM >=',color='green',params=[simpleActionEnum.PM_ADD,simpleActionEnum.PM_MINUS]),
            Constraint('pwSelector','PW >=',color='lightblue',params=[simpleActionEnum.PW_ADD,simpleActionEnum.PW_MINUS]),
            Constraint('pcSelector','PC >=',params=[simpleActionEnum.PC_ADD,simpleActionEnum.PC_MINUS]),
            Constraint('poSelector','PO >=',params=[simpleActionEnum.PO_ADD,simpleActionEnum.PO_MINUS]),
            Constraint('iniSelector','Initiative >=',params=[simpleActionEnum.INI_ADD,simpleActionEnum.INI_MINUS]),
            Constraint('ccSelector','CC >=',params=[simpleActionEnum.CC_ADD,simpleActionEnum.CC_MINUS]),
            Constraint('wisdomSelector','Sagesse >=',params=[simpleActionEnum.WIS_ADD,simpleActionEnum.WIS_MINUS]),
            Constraint('ppSelector','PP >=',params=[simpleActionEnum.PP_ADD,simpleActionEnum.PP_MINUS]),
            Constraint('willSelector','Volonté >=',params=[simpleActionEnum.WILL_ADD,simpleActionEnum.WILL_MINUS]),
            Constraint('blockSelector','Parade >=',params=[simpleActionEnum.BLOCK_ADD,simpleActionEnum.BLOCK_MINUS]),
            Constraint('lockSelector','Tacle >=',params=[simpleActionEnum.LOCK_ADD,simpleActionEnum.LOCK_MINUS]),
            Constraint('dodgeSelector','Esquive >=',params=[simpleActionEnum.DODGE_ADD,simpleActionEnum.DODGE_MINUS]),
            ResConstraint('resConstraint','Resistance >=',params=[])
        ])

        self.maximizeElemMasteryModel = WakfuConstraintSelectorTemplate([
            MasteryConstraint('fireSelector','Feu',default=0,min=0,max=1,params=[simpleActionEnum.FIRE_MASTERY_ADD,simpleActionEnum.FIRE_MASTERY_MINUS]),
            MasteryConstraint('waterSelector','Eau',default=1,min=0,max=1,params=[simpleActionEnum.WATER_MASTERY_ADD,simpleActionEnum.WATER_MASTERY_MINUS]),
            MasteryConstraint('airSelector','Air',default=1,min=0,max=1,params=[simpleActionEnum.AIR_MASTERY_ADD,simpleActionEnum.AIR_MASTERY_MINUS]),
            MasteryConstraint('earthSelector','Terre',default=0,min=0,max=1,params=[simpleActionEnum.EARTH_MASTERY_ADD,simpleActionEnum.EARTH_MASTERY_MINUS])
        ])

        self.maximizeOtherMasteryModel = WakfuConstraintSelectorTemplate([
            MasteryConstraint('critMasterySelector','maitrise critique',default=0,min=0,max=1,params=[simpleActionEnum.CRIT_MASTERY_ADD,simpleActionEnum.CRIT_MASTERY_MINUS]),
            MasteryConstraint('backMasterySelector','maitrise dos',default=0,min=0,max=1,params=[simpleActionEnum.BACK_MASTERY_ADD,simpleActionEnum.BACK_MASTERY_MINUS]),
            MasteryConstraint('meleeMasterySelector','maitrise melee',default=0,min=0,max=1,params=[simpleActionEnum.MELEE_MASTERY_ADD,simpleActionEnum.MELEE_MASTERY_MINUS]),
            MasteryConstraint('monoMasterySelector','maitrise mono',default=0,min=0,max=1,params=[simpleActionEnum.MONO_MASTERY_ADD,simpleActionEnum.MONO_MASTERY_MINUS]),
            MasteryConstraint('healMasterySelector','maitrise soin',default=0,min=0,max=1,params=[simpleActionEnum.HEAL_MASTERY_ADD,simpleActionEnum.HEAL_MASTERY_MINUS]),
            MasteryConstraint('distanceMasterySelector','maitrise distance',default=0,min=0,max=1,params=[simpleActionEnum.DISTANCE_MASTERY_ADD,simpleActionEnum.DISTANCE_MASTERY_MINUS]),
            MasteryConstraint('zoneMasterySelector','maitrise zone',default=0,min=0,max=1,params=[simpleActionEnum.ZONE_MASTERY_ADD,simpleActionEnum.ZONE_MASTERY_MINUS]),
            MasteryConstraint('berzerkMasterySelector','maitrise berzerk',default=0,min=0,max=1,params=[simpleActionEnum.BERSERK_MASTERY_ADD,simpleActionEnum.BERSERK_MASTERY_MINUS]),
            ])

        self.maximizeOtherModel = WakfuConstraintSelectorTemplate([
            RatioConstraint('blockMaximizeSelector','parade',default=0,min=0,max=1,ratio=10,params=[simpleActionEnum.BLOCK_ADD,simpleActionEnum.BLOCK_MINUS]),
            RatioConstraint('blockMaximizeSelector','tacle',default=0,min=0,max=1,ratio=1,params=[simpleActionEnum.LOCK_ADD,simpleActionEnum.LOCK_MINUS])
        ])

    def setStuffConstraints(self):
        # number of item constraint
        self.stuffConstraints.append(sum(var for var in settings.VARIABLES.values()) <= 14)

        #slot constraint
        self.stuffConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.HEAD) <=1)
        self.stuffConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.RING) <= 2)
        self.stuffConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.LEGS) <= 1)
        self.stuffConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.NECK) <= 1)
        self.stuffConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.BACK) <= 1)
        self.stuffConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.BELT) <= 1)
        self.stuffConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.CHEST) <= 1)
        self.stuffConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.SHOULDERS) <= 1)
        self.stuffConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.EMBLEMA) <= 1)
        self.stuffConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.PET) <= 1)
        self.stuffConstraints.append(createConstraintWithFunc(getEquipmentType,eqTypeEnum.MOUNT) <= 1)

    #    #Epic / relic constraint
        self.stuffConstraints.append(createConstraintWithFunc(getRarity,rarityEnum.EPIC) <=1)
        self.stuffConstraints.append(createConstraintWithFunc(getRarity,rarityEnum.RELIC) <=1)

    #    #waepon constraint
        self.stuffConstraints.append(createConstraintWithFunc(getWaeponType,"isPrimary") <=1)
        self.stuffConstraints.append(createConstraintWithFunc(getWaeponType,"isSecondary") <=1)
        self.stuffConstraints.append(createConstraintWithFunc(getWaeponType,"isTwoHanded") <=1)

        #at least one waepon
        self.stuffConstraints.append(createConstraintWithFunc(getWaeponType,"isPrimary")+
            createConstraintWithFunc(getWaeponType,"isSecondary") +
            createConstraintWithFunc(getWaeponType,"isTwoHanded") >=1)

        #Exclusive between twoHanded and primary
        self.stuffConstraints.append(createConstraintWithFunc(getWaeponType,"isPrimary")+
            createConstraintWithFunc(getWaeponType,"isTwoHanded") <=1)

        #Exclusive between twoHanded and secondary
        self.stuffConstraints.append(createConstraintWithFunc(getWaeponType,"isSecondary")+
            createConstraintWithFunc(getWaeponType,"isTwoHanded") <=1)
    #    #end waepon constraint

    def initSolver(self):

        self.stuffConstraints = []
        self.mazimize = None
        self.solver = pywraplp.Solver('Find optimal stuff based on constraints', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

        settings.VARIABLES={}

        constraints = self.simpleConstraintModel.getConstraints()

        rarity = [
         rarityEnum.WHITE if constraints[1].getValue() == 1 else -1,
         rarityEnum.GREEN if constraints[2].getValue() == 1 else -1,
         rarityEnum.ORANGE if constraints[3].getValue() == 1 else -1,
         rarityEnum.LEGENDARY if constraints[4].getValue() == 1 else -1,
         rarityEnum.BLUE if constraints[5].getValue() == 1 else -1,
         rarityEnum.EPIC if constraints[6].getValue() == 1 else -1,
         rarityEnum.RELIC if constraints[7].getValue() == 1 else -1,
        ]

        for key,item in settings.ITEMS_DATA.items():
           # remove shards from item list so far
           if item['definition']['item'].get('shardsParameters',0) != 0:
               continue
           if item['definition']['item']['level'] > constraints[0].getValue() :
               continue

           if item['definition']['item']['baseParameters']['rarity'] not in rarity:
               continue

           settings.VARIABLES[key]=self.solver.BoolVar(item['title']['fr']+str(item['definition']['item']['id']))


        self.setStuffConstraints()
        for constraint in self.stuffConstraints:
            self.solver.Add(constraint)

        for constraint in self.simpleConstraintModel.getConstraints():
            for i in constraint.createSolverConstraints():
                self.solver.Add(i)

        #Maximize section
        maximizeElemMasteryConstraint=self.maximizeElemMasteryModel.getConstraints()
        maximizeOtherMasteryConstraint=self.maximizeOtherMasteryModel.getConstraints()
        maximzieOtherConstraint=self.maximizeOtherModel.getConstraints()

        nbElem = sum(var.getValue() for var in maximizeElemMasteryConstraint )
        maximize =SumArray([])

        if nbElem !=0 :
            for constraint in maximizeElemMasteryConstraint:
                for i in constraint.createSolverConstraints():
                        maximize+=i
            maximize+=createParamsConstraint(paramsActionEnum.RANDOM_NUMBER_MASTERY_ADD,paramsActionEnum.RANDOM_NUMBER_MASTERY_MINUS,nbElem)
            maximize+=createSimpleAddSubstractConstraint(simpleActionEnum.ELEM_MASTERY_ADD,simpleActionEnum.ELEM_MASTERY_MINUS,nbElem)
            for constraint in maximizeOtherMasteryConstraint:
                for i in constraint.createSolverConstraints():
                    maximize+=i*nbElem
        else:
            for constraint in maximzieOtherConstraint:
                for i in constraint.createSolverConstraints():
                    maximize+=i
        self.solver.Maximize(maximize)
        # end of Maximize section

    @Slot(result=QAbstractItemModel)
    def getConstraintModel(self):
        return self.simpleConstraintModel

    @Slot(result=QAbstractItemModel)
    def getElemMasteryMaximizeModel(self):
        return self.maximizeElemMasteryModel

    @Slot(result=QAbstractItemModel)
    def getOtherMasteryMaximizeModel(self):
        return self.maximizeOtherMasteryModel

    @Slot(result=QAbstractItemModel)
    def getOtherMaximizeModel(self):
        return self.maximizeOtherModel

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
                  myList.append({'id': key, 'name': settings.ITEMS_DATA[key]['title']['fr']})
        else:
          print('The solver could not find an optimal solution.')

        settings.OPTIMIZED_ITEM_LIST = myList








