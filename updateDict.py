import copy

def updateDict(base,new,overwrite=False,verbose=False):
    base = copy.deepcopy(base)
    if base == new: return(base)
    # more comprehensive way to update items in a nested dict
    for key,value in new.items():
        if type(base) is dict and key not in base.keys():
            if verbose: print('setting: ',key,' = ',base,'\n to: ',key,' = ',value)
            base[key]=value
        elif type(value) is dict and type(base[key]) is dict:
            base[key] = updateDict(base[key],value,overwrite,verbose)
        elif overwrite == True and base[key]!= value:
            if verbose: print('setting: ',key,' = ',base[key],'\n to: ',key,' = ',value)
            base[key] = value
        elif overwrite == 'append' and type(base[key]) is list:
            if type(base[key][0]) is not list and type(value) is list:
                base[key] = [base[key]]
            if verbose: print('adding: ',value,'\n to: ',key,' = ',base[key])
            base[key].append(value)
        elif overwrite == 'append' and type(base[key]) is not list:
            base[key] = [base[key]]
            if verbose: print('adding: ',value,'\n to: ',key,' = ',base[key])
            base[key].append(value)
        elif base[key] is None and value is not None:
            if verbose: print('setting: ',key,' = ',base[key],'\n to: ',key,' = ',value)
            base[key] = value
        elif base[key] != value:
            if verbose: print(f'overwrite = {overwrite} will not update matching keys: ',base[key],value)
    return(base) 