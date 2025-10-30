# A small set of functions for handlign common tasks with dictionary objects
import os
import yaml
import json
import copy
from .log import log
ymlStartMarker = '\n---\n'

# Convert a dataclass to a dictionary
# Default settings will give same as built in __dict__
# Options:
# 1. repr:
#   * None - do not filter by repr
#   * True/False  - only output where repr == True/False
# 2. inheritance:
#   * True - include inherited fields
#   * False - exclude inherited fields


def dcToDict(dc,repr=None,inheritance=True):
    if inheritance:
        if repr:
            return({k:v for k,v in dc.__dict__.items() if k in dc.__dataclass_fields__ and dc.__dataclass_fields__[k].repr})
        elif repr is None:
            return({k:v for k,v in dc.__dict__.items() if k in dc.__dataclass_fields__})
        else:
            return({k:v for k,v in dc.__dict__.items() if k in dc.__dataclass_fields__ and not dc.__dataclass_fields__[k].repr})
    else:
        if repr:
            return({k:dc.__dict__[k] for k in dc.__annotations__.keys() if k in dc.__dataclass_fields__ and dc.__dataclass_fields__[k].repr})
        elif repr is None:
            return({k:dc.__dict__[k] for k in dc.__annotations__.keys() if k in dc.__dataclass_fields__})
        else:
            return({k:dc.__dict__[k] for k in dc.__annotations__.keys() if k in dc.__dataclass_fields__ and not dc.__dataclass_fields__[k].repr})

# Load a dictionary a .json or .yml file
# Preserve the header in a yaml file if desired
def loadDict(fileName,template = {},header=None,verbose=False,ln=False):
    fileName = os.path.abspath(fileName)
    if os.path.isfile(fileName):
        if fileName.endswith('.yml') or fileName.endswith('.yaml'):
            # check for header in yaml file
            with open(fileName) as file:
                tmp = file.read()
                if ymlStartMarker in tmp:
                    header = tmp.split(ymlStartMarker)[0]
                else:
                    header = None
            with open(fileName) as file:
                out = yaml.safe_load(file)
        elif fileName.endswith('.json'):
            with open(fileName) as file:
                out = json.load(file)
        else:
            log(f'File format not supported for {fileName}',kill=True)
    else:
        try:
            log(f"Does not exist:\n{fileName}\nCreating new file using default or user-provided template:\n{template}",ln=ln,verbose=verbose)
        except:
            log(f"Does not exist:\n{fileName}\nCreating new file using default or user-provided template:\n",ln=ln,verbose=verbose)
            pass
        out = copy.deepcopy(template)
        saveDict(out,fileName)
    return(out,header)

# Save a dictionary to json or yaml format
# Preserve yaml header if desired
def saveDict(obj,fileName,header=None,sort_keys=False,indent=None,anchors=False):
    if os.path.split(fileName)[0] == '':
        pass
    elif not os.path.isdir(os.path.split(fileName)[0]):
        os.makedirs(os.path.split(fileName)[0])

    with open(fileName,'w') as file:
        if fileName.endswith('.yml'):
            if header:
                header = '\n'.join([h if h.startswith('#') else '# '+h for h in header.split('\n')])
                file.write(header+ymlStartMarker)
            if anchors:
                yaml.safe_dump(obj,file,sort_keys=sort_keys,default_flow_style=False)
            else:
                yaml.safe_dump(obj,file,sort_keys=sort_keys)
        if fileName.endswith('.json'):
            json.dump(obj,file,indent=indent)

