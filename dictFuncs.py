# A small set of functions for handlign common tasks with dictionary objects
import os
import sys
# import yaml
import json
from typing import Iterable
from .log import log
import copy
ymlStartMarker = '\n---\n'


from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

yaml = YAML()


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
                out = yaml.load(file)
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
                yaml.dump(obj,file)
            else:
                yaml.dump(obj,file)
            # if anchors:
            #     yaml.safe_dump(obj,file,sort_keys=sort_keys,default_flow_style=False)
            # else:
            #     yaml.safe_dump(obj,file,sort_keys=sort_keys)
        if fileName.endswith('.json'):
            json.dump(obj,file,indent=indent)



# Stashing here in case needed for later.  
def unpackDict(Tree,format=os.path.sep,limit=None):
    # recursive function to condense a nested dict by concatenating keys to a string
    def unpack(child,parent=None,root=None,format=None,limit=None):
        pth = {}
        if type(child) is dict and (limit is None or limit >= 0) and child:
            if limit is not None:
                limit -= 1
            for key,value in child.items():
                if parent is None:
                    pass
                else:
                    key = format.join([parent,key])
                if type(value) is not dict or (limit is not None and limit < 0) or not value:
                    pth[key] = unpack(value,key,root,format,limit)
                else:
                    pth = pth | unpack(value,key,root,format,limit)
        else:
            if type(child) is not dict or (limit is not None and limit < 0) or not child:
                return(child)
            else:
                sys.exit('Error in file tree unpack')
        return(pth)
    return(unpack(Tree,format=format,limit=limit))

def packDict(itemList,format=os.path.sep,limit=None,order=-1,base=None,fill=None,verbose=False):
    # recursive function to generate nested dict from list of strings, splitting by sep
    Tree = {}
    if type(itemList) is list:
        if fill == 'key':
            itemList = {key:key for key in itemList}
        elif type(fill) is list:
            itemList = {key:f for key,f in zip(itemList,fill)}
        else:
            itemList = {key:fill for key in itemList}
    elif type(itemList) is not dict:
        itemList = {itemList:fill}
    for key,value in itemList.items():
        if base is None:
            b = key.split(format)
        else:
            b = [base] + [b for b in key.replace(base,'').split(format) if b != '']
        if order == -1:
            if limit is None: lm = len(b)+order
            else: lm = limit
            start = len(b)
            end = max(0,len(b)+lm*order+order)
            for i in range(start,end,order):
                if i == start:
                    subTree = {b[i+order]:value}
                elif i>end+1:
                    subTree =  {b[i+order]:subTree}
                else:
                    subTree = {format.join(b[:i]):subTree}
        else:
            if limit is None: lm = len(b)
            else: lm = limit
            start = 0
            end = min(lm+1,len(b))
            for i in range(start,end,order):
                if i == start:
                    subTree = {format.join(b[end-1:]):value}
                else:
                    subTree = {b[end-1-i]:subTree}
        Tree = updateDict(Tree,subTree,overwrite='append',verbose=verbose)
    return(Tree)

# more comprehensive way to update items in a nested dict compared to the base|new operator

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