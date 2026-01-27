# A small set of functions for handlign common tasks with dictionary objects
import os
import yaml
import json
from typing import Iterable
from .log import log
ymlStartMarker = '\n---\n'

# Convert a dataclass to a dictionary
# Can give similar output as built in __dict__ if run with (repr=False) but modified order (child fields before parent fields)
# Or give more advanced output by excluding fields based on field properites
# For now, does not resolve MRO beyond first parent, all ineherited fields will follow default order
# Options:
# 1. repr:
#   * False - do not filter by repr
#   * True  - only output
# 2. inheritance:
#   * True - include inherited fields
#   * False - exclude inherited fields
# 3. keepNull
#   * True - include all values
#   * False - exclude values if they are None

def dcToDict(dc,repr=True,inheritance=True,keepNull=True,majorOrder=1,minorOrder=1):
    fields = dc.__dataclass_fields__
    # Keys of child class
    if inheritance:
        # Keys of child and all parent classes with inverse order of MRO (children last)
        outputKeys = [n for m in type(dc).__mro__[::majorOrder] if hasattr(m,'__annotations__') for n in list(m.__annotations__)[::minorOrder]]        
    else:
        # Only child keys
        outputKeys = list(dc.__annotations__)
    
    # If wanting to add functionality later, its here.  Could override keepNull=True
    # optional = {k:False if 'optional' not in dc.__dataclass_fields__[k].metadata else dc.__dataclass_fields__[k].metadata['optional'] for k in outputKeys}
    optional = {k:True for k in outputKeys}

    cleanOutput = {
        k: getattr(dc, k) for k in outputKeys
        if hasattr(dc, k) and
        (keepNull or not optional[k] or getattr(dc, k) is not None) and # Apply null filter if applicable
        (fields[k].repr or not repr) # Apply repr filter if applicable
    }
    # Move iterables to back to increase readability of yaml files
    toBack = {}
    toFront = {}
    for key,value in cleanOutput.items():
        if type(value) is not str and isinstance(value,Iterable):
            toBack[key] = value
        else:
            toFront[key] = value
    finalOutput = toFront | toBack
    return finalOutput



# Load a dictionary a .json or .yml file
# Preserve the header in a yaml file if desired
def loadDict(fileName=None,template = {},returnHeader=False,verbose=False,traceback=False):
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
                header = None
        else:
            log(f'File format not supported for {fileName}',kill=True)
    else:
        log(f'Does not exist:\n {fileName}',kill=True)
    if returnHeader:
        return(out,header)
    else:
        return(out)

# Save a dictionary to json or yaml format
# Preserve yaml header if desired
def saveDict(obj,fileName,header=None,sort_keys=False,indent=None,anchors=False):
    if os.path.split(fileName)[0] == '':
        pass
    elif not os.path.isdir(os.path.split(fileName)[0]):
        os.makedirs(os.path.split(fileName)[0])

    with open(fileName,'w') as file:
        # breakpoint()
        if fileName.endswith('.yml'):
            # print(fileName)
            if header:
                header = '\n'.join([h if h.startswith('#') else '# '+h for h in header.split('\n')])
                file.write(header+ymlStartMarker)
            if anchors:
                yaml.safe_dump(obj,file,sort_keys=sort_keys,default_flow_style=False)
            else:
                yaml.safe_dump(obj,file,sort_keys=sort_keys)
        if fileName.endswith('.json'):
            json.dump(obj,file,indent=indent)

