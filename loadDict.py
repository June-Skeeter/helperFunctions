import os
import yaml
import json
from .log import log
from .saveDict import saveDict
# read a dict from file in either .json or .yml format
def loadDict(file,verbose=False):
    file = os.path.abspath(file)
    if os.path.isfile(file):
        if file.endswith('.yml'):
            with open(file) as f:
                out = yaml.safe_load(f)
        elif file.endswith('.json'):
            with open(file) as f:
                out = json.load(f)   
    else:
        log(f"{file}\n\ndoes not exist, creating empty file",ln=False,verbose=verbose)
        out = {}
        saveDict(out,file)
    return(out)
