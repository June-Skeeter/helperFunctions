import os
import yaml
import json
from . import log
# read a dict from file in either .json or .yml format
def loadDict(file,verbose=False,safemode=False):
    file = os.path.abspath(file)
    if os.path.isfile(file):
        if file.endswith('.yml'):
            with open(file) as f:
                out = yaml.safe_load(f)
        elif file.endswith('.json'):
            with open(file) as f:
                out = json.load(f)   
    elif not safemode:
        if verbose: log(f"{file}\ndoes not exist, creating empty file")
        out = {}
        # saveDict(out,file)
    # elif verbose:
    #     out = None
    #     print(f"{file} does not exist")
    # log(file,fn=False,verbose=verbose)
    # log(out,fn=False,verbose=verbose)
    return(out)
