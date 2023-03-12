import enum

def initGlobal():
    global ITEMS_DATA
    ITEMS_DATA={}

    global ITEM_PROPERTIES_DATA
    ITEM_PROPERTIES_DATA={}

    global EQUIPMENT_ITEM_TYPES_DATA
    EQUIPMENT_ITEM_TYPES_DATA={}

    global ACTION_DATA
    ACTION_DATA={}

    global VARIABLES
    VARIABLES={}

    global OPTIMIZED_ITEM_LIST
    OPTIMIZED_ITEM_LIST = {}

class eqTypeEnum(enum.IntEnum):
    RING = 103
    LEGS = 119
    NECK = 120
    BACK = 132
    BELT = 133
    HEAD = 134
    CHEST = 136
    SHOULDERS = 138
    PET = 582
    MOUNT = 611
    EMBLEMA = 646
    COSTUME = 647

#Should do parent stuff again
#ACCESSORY=480 / ACCESSORY=537 / EMBLEMA = 646

class rarityEnum(enum.IntEnum):
    WHITE = 1
    GREEN = 2
    ORANGE = 3
    LEGENDARY = 4
    RELIC = 5
    BLUE = 6
    EPIC = 7

class waeponEnum(enum.Enum):
    PRIMARY = "isPrimary"
    SECONDARY = "isSecondary"
    TWO_HANDED = "isTwoHanded"

class simpleActionEnum(enum.IntEnum):
    PV_ADD=20
    PV_MINUS=21

    PA_ADD=31
    PA_MINUS=56

    PM_ADD=41
    PM_MINUS=57

    PO_ADD=160
    PO_MINUS=161

    PW_ADD=191
    PW_MINUS=192

    PC_ADD=184
    PC_MINUS=-1

    INI_ADD=171
    INI_MINUS=172

    CC_ADD=150
    CC_MINUS=168

    WIS_ADD=166
    WIS_MINUS=-1

    PP_ADD=162
    PP_MINUS=-1

    WILL_ADD=177
    WILL_MINUS=-1

    BLOCK_ADD=875
    BLOCK_MINUS=876

    LOCK_ADD=173
    LOCK_MINUS=174

    DODGE_ADD=175
    DODGE_MINUS=176

    FIRE_MASTERY_ADD=122
    FIRE_MASTERY_MINUS=132

    WATER_MASTERY_ADD=124
    WATER_MASTERY_MINUS=-1 #???? NO REMOVE OF WATER MASTERY

    AIR_MASTERY_ADD=125
    AIR_MASTERY_MINUS=-1

    EARTH_MASTERY_ADD=123
    EARTH_MASTERY_MINUS=-1

    ELEM_MASTERY_ADD=120
    ELEM_MASTERY_MINUS=130

class paramsActionEnum(enum.IntEnum):

    RANDOM_NUMBER_MASTERY_ADD=1068
    RANDOM_NUMBER_MASTERY_MINUS=-1
#ID=39 working quite strange, should take into action
