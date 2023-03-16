# This Python file uses the following encoding: utf-8
from typing import List
from solver import createSimpleAddSubstractConstraint,createParamsConstraint,createLevelConstraint
from settings import paramsActionEnum,simpleActionEnum
import math

class Constraint:

    def __init__(self,name: str,text: str,params: List,default: int=0,color: str='black',min: int=0,max: int=9999,ratio: int=1):
        self.setName(name)
        self.setColor(color)
        self.setMin(min)
        self.setMax(max)
        self.setValue(default)
        self.setDefault(default)
        self.setText(text)
        self.setParams(params)

    def setName(self,name: str):
        self.name=name

    def setColor(self,color: str):
        self.color=color

    def setMin(self,min: int):
        self.min=min

    def setMax(self,max: int):
        self.max=max

    def setValue(self,value: int):
        self.value=int(value)

    def setDefault(self,default: str):
        self.default=default

    def setText(self,text: str):
        self.text=text

    def setParams(self,params: List):
        self.params=params

    def setRatio(self,ratio: int):
        self.ratio=ratio

    def getName(self):
        return self.name

    def getColor(self):
        return self.color

    def getMin(self):
        return self.min

    def getMax(self):
        return self.max

    def getDefault(self):
        return self.default

    def getValue(self):
        return self.value

    def getText(self):
        return self.text

    def getParams(self):
        return self.params

    def getRatio(self):
        return self.ratio

    def createSolverConstraints(self,ratio=None):
        if self.getValue() == self.getDefault():
            return []
        return [createSimpleAddSubstractConstraint(self.getParams()[0],self.getParams()[1]) >= self.getValue()]

class LevelConstraint(Constraint):
    def createSolverConstraints(self,ratio=None):
        return []

class RarityConstraint(Constraint):
    def createSolverConstraints(self,ratio=None):
        return []

class ResConstraint(Constraint):
    def createSolverConstraints(self,ratio=None):

        target = -((self.getValue()/100)-1)
        resNumber = math.log(target,0.8)*100

        return[
            createSimpleAddSubstractConstraint(simpleActionEnum.FIRE_RES_ADD,simpleActionEnum.FIRE_RES_MINUS)+
            createSimpleAddSubstractConstraint(simpleActionEnum.ELEM_RES_ADD,simpleActionEnum.ELEM_RES_MINUS_UNCAPED)+
            150+
            createParamsConstraint(paramsActionEnum.RANDOM_NUMBER_RES_ADD,paramsActionEnum.RANDOM_NUMBER_RES_MINUS,4)/4 >= resNumber,

            createSimpleAddSubstractConstraint(simpleActionEnum.AIR_RES_ADD,simpleActionEnum.AIR_RES_MINUS)+
            createSimpleAddSubstractConstraint(simpleActionEnum.ELEM_RES_ADD,simpleActionEnum.ELEM_RES_MINUS_UNCAPED)+
            150+
            createParamsConstraint(paramsActionEnum.RANDOM_NUMBER_RES_ADD,paramsActionEnum.RANDOM_NUMBER_RES_MINUS,4)/4 >= resNumber,

            createSimpleAddSubstractConstraint(simpleActionEnum.WATER_RES_ADD,simpleActionEnum.WATER_RES_MINUS)+
            createSimpleAddSubstractConstraint(simpleActionEnum.ELEM_RES_ADD,simpleActionEnum.ELEM_RES_MINUS_UNCAPED)+
            150+
            createParamsConstraint(paramsActionEnum.RANDOM_NUMBER_RES_ADD,paramsActionEnum.RANDOM_NUMBER_RES_MINUS,4)/4 >= resNumber,

            createSimpleAddSubstractConstraint(simpleActionEnum.EARTH_RES_ADD,simpleActionEnum.EARTH_RES_MINUS)+
            createSimpleAddSubstractConstraint(simpleActionEnum.ELEM_RES_ADD,simpleActionEnum.ELEM_RES_MINUS_UNCAPED)+
            150+
            createParamsConstraint(paramsActionEnum.RANDOM_NUMBER_RES_ADD,paramsActionEnum.RANDOM_NUMBER_RES_MINUS,4)/4 >= resNumber]
class MasteryConstraint(Constraint):
    def createSolverConstraints(self,ratio=None):
        if self.getValue() == 0:
            return []
        return [createSimpleAddSubstractConstraint(self.getParams()[0],self.getParams()[1])]

class RatioConstraint(Constraint):
    def createSolverConstraints(self,ratio=None):
        if self.getValue() == 0:
            return []
        return [createSimpleAddSubstractConstraint(self.getParams()[0],self.getParams()[1])*self.getRatio()]
