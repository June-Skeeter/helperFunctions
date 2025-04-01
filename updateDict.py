# more comprehensive way to update items in a nested dict compared to the base|new operator
from .log import log
import copy
def updateDict(base,new,overwrite=False,verbose=False):
    base = copy.deepcopy(base)
    if base == new: return(base)
    for key,value in new.items():
        if type(base) is dict and key not in base.keys():
            log(['setting: ',key,' = ',base,'\n to: ',key,' = ',value],verbose=verbose)
            base[key]=value
        elif type(value) is dict and type(base[key]) is dict:
            base[key] = updateDict(base[key],value,overwrite,verbose)
        elif overwrite == True and base[key]!= value:
            log(['setting: ',key,' = ',base[key],'\n to: ',key,' = ',value],verbose=verbose)
            base[key] = value
        elif overwrite == 'append' and type(base[key]) is list:
            log(['adding: ',value,'\n to: ',key,' = ',base[key]],verbose=verbose)
            if type(base[key][0]) is not list and type(base[key][0]) is not dict and type(value) is list:
                base[key] = [base[key]]
            base[key]=base[key] + value
        elif overwrite == 'append' and type(base[key]) is not list and base[key] != value:
            base[key] = [base[key]]
            log(['adding: ',value,'\n to: ',key,' = ',base[key]],verbose=verbose)
            base[key].append(value)
        elif base[key] is None and value is not None:
            log(['setting: ',key,' = ',base[key],'\n to: ',key,' = ',value],verbose=verbose)
            base[key] = value
        elif base[key] != value:
            log([f'overwrite = {overwrite} will not update matching keys: ',base[key],value],verbose=verbose)
    return(base) 