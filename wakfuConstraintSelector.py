# This Python file uses the following encoding: utf-8

from PySide6.QtQml import QmlElement
from PySide6.QtCore import Slot,QObject,Signal,QAbstractItemModel

import json
import settings
from settings import eqTypeEnum
from settings import rarityEnum
from settings import simpleActionEnum
from settings import paramsActionEnum
from solver import createConstraintWithFunc,getEquipmentType,getRarity,getWaeponType,createSimpleAddSubstractConstraint,createParamsConstraint,createLevelConstraint
from ortools.linear_solver import pywraplp
from ortools.linear_solver.pywraplp import SumArray
from wakfuConstraintSelectorTemplate import WakfuConstraintSelectorTemplate
from constraint import Constraint,ResConstraint,LevelConstraint,RarityConstraint,MasteryConstraint,RatioConstraint
from stat_profile_manager import CONSTRAINT_STAT_MAP, resistance_percent_to_raw
import stat_profile_manager
import math


QML_IMPORT_NAME = "wakfuConstraintSelector"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class WakfuConstraintSelector(QObject):

    excludedItemsChanged = Signal()
    forcedItemsChanged = Signal()

    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.constraintValueFromUi = {}
        self._active_profile_id = ""
        self._excluded_item_ids = set()
        self._forced_item_ids = set()

        self.simpleConstraintModel = WakfuConstraintSelectorTemplate([
            LevelConstraint('levelSelector','Level <=',params=[],default=230,min=1,max=999),
            RarityConstraint('rarityCommonSelector','Common ==',params=[],default=1,min=0,max=1,color='white'),
            RarityConstraint('rarityRareSelector','Rare ==',params=[],default=1,min=0,max=1,color='green'),
            RarityConstraint('rarityMythicalSelector','Mythical ==',params=[],default=1,min=0,max=1,color='orange'),
            RarityConstraint('rarityLegendarySelector','Legendary ==',params=[],default=1,min=0,max=1,color='yellow'),
            RarityConstraint('rarityMemorySelector','Memory ==',params=[],default=1,min=0,max=1,color='lightblue'),
            RarityConstraint('rarityEpicSelector','Epic ==',params=[],default=1,min=0,max=1,color='#f9a8d4'),
            RarityConstraint('rarityRelicSelector','Relic ==',params=[],default=1,min=0,max=1,color='#6d28d9'),
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
            ResConstraint('resConstraint','Resistance >=',params=[],min=0,max=99)
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
            MasteryConstraint('healMasterySelector','maitrise soin',default=0,min=0,max=1,params=[simpleActionEnum.HEAL_MASTERY_ADD,simpleActionEnum.HEAL_MASTERY_MINUS]),
            MasteryConstraint('distanceMasterySelector','maitrise distance',default=0,min=0,max=1,params=[simpleActionEnum.DISTANCE_MASTERY_ADD,simpleActionEnum.DISTANCE_MASTERY_MINUS]),
            MasteryConstraint('berzerkMasterySelector','maitrise berzerk',default=0,min=0,max=1,params=[simpleActionEnum.BERSERK_MASTERY_ADD,simpleActionEnum.BERSERK_MASTERY_MINUS]),
            ])

        self.maximizeOtherModel = WakfuConstraintSelectorTemplate([
            RatioConstraint('blockMaximizeSelector','parade',default=0,min=0,max=1,ratio=10,params=[simpleActionEnum.BLOCK_ADD,simpleActionEnum.BLOCK_MINUS]),
            RatioConstraint('lockMaximizeSelector','tacle',default=0,min=0,max=1,ratio=1,params=[simpleActionEnum.LOCK_ADD,simpleActionEnum.LOCK_MINUS])
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
        # PET slot: familier (582) and porte-bonheur (849, added in 1.92)
        # share the same in-game position → at most one across the two.
        self.stuffConstraints.append(
            createConstraintWithFunc(getEquipmentType, eqTypeEnum.PET)
            + createConstraintWithFunc(getEquipmentType, eqTypeEnum.LUCKY_CHARM)
            <= 1
        )
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

        # All-or-none item groups (e.g. Épée + Anneau d'Amakna).
        # Loaded from data_overrides/item_pairings.json.
        for group in settings.ITEM_PAIRINGS:
            present = [i for i in group["items"] if i in settings.VARIABLES]
            if len(present) < len(group["items"]):
                # At least one group member was filtered out (level/rarity/excluded)
                # → the group can't be completed, so forbid the present members.
                print(f"[pairings] group {group['name']!r} disabled: "
                      f"{len(present)}/{len(group['items'])} members in pool "
                      f"(check level/rarity/exclusion filters)")
                for iid in present:
                    self.stuffConstraints.append(settings.VARIABLES[iid] == 0)
                continue
            anchor = settings.VARIABLES[present[0]]
            for iid in present[1:]:
                self.stuffConstraints.append(settings.VARIABLES[iid] == anchor)

        # Forced items: V[id] == 1. Forced ids always end up in VARIABLES
        # (filters bypassed above), but guard defensively.
        for iid in self._forced_item_ids:
            if iid in settings.VARIABLES:
                self.stuffConstraints.append(settings.VARIABLES[iid] == 1)

    def initSolver(self):

        self.stuffConstraints = []
        self.mazimize = None
        self.solver = pywraplp.Solver('Find optimal stuff based on constraints', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

        settings.VARIABLES={}

        constraints = self.simpleConstraintModel.getConstraints()

        # Rarity toggles are matched by constraint name (not position) so a
        # reorder / insertion elsewhere in simpleConstraintModel can't silently
        # break the filter.
        rarity_by_selector = {
            "rarityCommonSelector":    rarityEnum.WHITE,
            "rarityRareSelector":      rarityEnum.GREEN,
            "rarityMythicalSelector":  rarityEnum.ORANGE,
            "rarityLegendarySelector": rarityEnum.LEGENDARY,
            "rarityMemorySelector":    rarityEnum.BLUE,
            "rarityEpicSelector":      rarityEnum.EPIC,
            "rarityRelicSelector":     rarityEnum.RELIC,
        }
        rarity = {
            rarity_by_selector[c.getName()]
            for c in constraints
            if c.getName() in rarity_by_selector and c.getValue() == 1
        }

        # Find the level cap the same way.
        level_cap = next(c.getValue() for c in constraints
                         if c.getName() == "levelSelector")

        for key,item in settings.ITEMS_DATA.items():
           # remove shards from item list so far
           if item['definition']['item'].get('shardsParameters',0) != 0:
               continue

           # Forced items bypass level / rarity / exclusion filters — user intent wins.
           if key not in self._forced_item_ids:
               if item['definition']['item']['level'] > level_cap:
                   continue
               if item['definition']['item']['baseParameters']['rarity'] not in rarity:
                   continue
               if key in self._excluded_item_ids:
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
            maximize+=createSimpleAddSubstractConstraint(simpleActionEnum.ELEM_MASTERY_ADD,simpleActionEnum.ELEM_MASTERY_MINUS)*nbElem
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

    @Slot(result=int)
    def elemMasteryActiveCount(self):
        """Number of enabled elemental-mastery toggles (fire/water/air/earth)."""
        return sum(1 for c in self.maximizeElemMasteryModel.getConstraints()
                   if c.getValue() == 1)

    @Slot(result=int)
    def otherMaximizeActiveCount(self):
        """Number of enabled parade/tacle toggles (mutually exclusive with elem)."""
        return sum(1 for c in self.maximizeOtherModel.getConstraints()
                   if c.getValue() == 1)

    @Slot(int)
    def selectOnlyOtherMaximize(self, index):
        """Radio-select: enable only the given index in maximizeOtherModel,
        turn all others off. Used by the parade/tacle chips."""
        m = self.maximizeOtherModel
        for i, c in enumerate(m.getConstraints()):
            c.setValue(1 if i == index else 0)
        m.beginResetModel()
        m.endResetModel()

    @Slot(result=str)
    def exportConstraints(self):
        """Export all constraint values as a JSON string (name -> value)."""
        data = {}
        for model in [self.simpleConstraintModel, self.maximizeElemMasteryModel,
                       self.maximizeOtherMasteryModel, self.maximizeOtherModel]:
            for constraint in model.getConstraints():
                data[constraint.getName()] = constraint.getValue()
        return json.dumps(data)

    @Slot(str)
    def importConstraints(self, json_str):
        """Restore constraint values from a JSON string and refresh the UI."""
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            return

        for model in [self.simpleConstraintModel, self.maximizeElemMasteryModel,
                       self.maximizeOtherMasteryModel, self.maximizeOtherModel]:
            for i, constraint in enumerate(model.getConstraints()):
                if constraint.getName() in data:
                    constraint.setValue(data[constraint.getName()])
            model.beginResetModel()
            model.endResetModel()

    @Slot(str)
    def setActiveProfile(self, profile_id):
        self._active_profile_id = profile_id

    @Slot()
    def clearActiveProfile(self):
        self._active_profile_id = ""

    @Slot(result=str)
    def getActiveProfileId(self):
        return self._active_profile_id

    @Slot(int)
    def addExcludedItem(self, item_id):
        self._excluded_item_ids.add(item_id)
        self.excludedItemsChanged.emit()

    @Slot(int)
    def removeExcludedItem(self, item_id):
        self._excluded_item_ids.discard(item_id)
        self.excludedItemsChanged.emit()

    @Slot()
    def clearExcludedItems(self):
        self._excluded_item_ids.clear()
        self.excludedItemsChanged.emit()

    @Slot(int, result=bool)
    def isItemExcluded(self, item_id):
        return item_id in self._excluded_item_ids

    @Slot(result=int)
    def excludedItemCount(self):
        return len(self._excluded_item_ids)

    @Slot(result=str)
    def getExcludedItemsJson(self):
        return json.dumps(list(self._excluded_item_ids))

    @Slot(str)
    def setExcludedItemsFromJson(self, json_str):
        try:
            ids = json.loads(json_str)
            self._excluded_item_ids = set(ids)
        except (json.JSONDecodeError, ValueError, TypeError):
            self._excluded_item_ids = set()
        self.excludedItemsChanged.emit()

    # ── Forced items (must be picked, bypass level/rarity filters) ──

    @Slot(int)
    def addForcedItem(self, item_id):
        self._forced_item_ids.add(item_id)
        # Forcing wins over excluding: keep the two sets disjoint.
        self._excluded_item_ids.discard(item_id)
        self.forcedItemsChanged.emit()
        self.excludedItemsChanged.emit()

    @Slot(int)
    def removeForcedItem(self, item_id):
        self._forced_item_ids.discard(item_id)
        self.forcedItemsChanged.emit()

    @Slot()
    def clearForcedItems(self):
        self._forced_item_ids.clear()
        self.forcedItemsChanged.emit()

    @Slot(int, result=bool)
    def isItemForced(self, item_id):
        return item_id in self._forced_item_ids

    @Slot(result=int)
    def forcedItemCount(self):
        return len(self._forced_item_ids)

    @Slot(result=str)
    def getForcedItemsJson(self):
        return json.dumps(list(self._forced_item_ids))

    @Slot(str)
    def setForcedItemsFromJson(self, json_str):
        try:
            ids = json.loads(json_str)
            self._forced_item_ids = set(ids)
        except (json.JSONDecodeError, ValueError, TypeError):
            self._forced_item_ids = set()
        self.forcedItemsChanged.emit()

    @Slot(int, result=str)
    def getItemName(self, item_id):
        item = settings.ITEMS_DATA.get(item_id)
        if item:
            return item.get('title', {}).get('fr', str(item_id))
        return str(item_id)

    def _applyStatProfile(self):
        """Apply base stats from the active profile to all constraints."""
        stats = {}
        if self._active_profile_id:
            profile = stat_profile_manager.get_profile(self._active_profile_id)
            if profile:
                stats = profile.get("stats", {})

        for constraint in self.simpleConstraintModel.getConstraints():
            stat_key = CONSTRAINT_STAT_MAP.get(constraint.getName())
            if stat_key and stat_key in stats:
                value = stats[stat_key]
                if constraint.getName() == "resConstraint":
                    value = resistance_percent_to_raw(value)
                constraint.setBaseValue(value)
            else:
                constraint.setBaseValue(0)

    @Slot()
    def solve(self):

        self._applyStatProfile()
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
                  myList.append(key)
        else:
          print('The solver could not find an optimal solution.')

        settings.OPTIMIZED_ITEM_LIST = myList








