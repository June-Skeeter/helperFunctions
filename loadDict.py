import os
import sys
import yaml
import json
import copy
from .log import log
from .saveDict import saveDict



# read a dict from file in either .json or .yml format
def loadDict(file,template = {},verbose=False,ln=False):
    file = os.path.abspath(file)
    if os.path.isfile(file):
        if file.endswith('.yml') or file.endswith('.yaml'):
            with open(file) as f:
                out = yaml.safe_load(f)
        elif file.endswith('.json'):
            with open(file) as f:
                out = json.load(f)
        else:
            sys.exit(f'File format not supported for {file}')
    else:
        try:
            log(f"Does not exist:\n{file}\nCreating new file using default or user-provided template:\n{template}",ln=True,verbose=verbose)
        except:
            log(f"Does not exist:\n{file}\nCreating new file using default or user-provided template:\n",ln=True,verbose=verbose)
            pass
        out = copy.deepcopy(template)
        saveDict(out,file)
    return(out)
