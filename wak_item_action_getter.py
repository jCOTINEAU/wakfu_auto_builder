import settings

def safeget(dct, *keys):
    for key in keys:
        try:
            dct = dct[key]
        except KeyError:
            return None
    return dct

def getEquipEffectValue(dct,equipId):
    var = safeget(dct,"definition","equipEffects",equipId,"effect","definition","params")
    if var != None:
        return var[0]
    return 0
