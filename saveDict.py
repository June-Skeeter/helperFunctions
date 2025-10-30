import os
import yaml
import json

from .log import log
log('Note to self: this is depreciated, use dictFuncs.dcToDcit instead',fn=True,ln=True,kill=True)

# save a dict (obj) to a file (outputPath) in either .json or .yml format
def saveDict(obj,outputPath,sort_keys=False,indent=None,anchors=False):
    if os.path.split(outputPath)[0] == '':
        pass
    elif not os.path.isdir(os.path.split(outputPath)[0]):
        os.makedirs(os.path.split(outputPath)[0])
    with open(outputPath,'w') as file:
        if outputPath.endswith('.yml'):
            if anchors:
                yaml.safe_dump(obj,file,sort_keys=sort_keys,default_flow_style=False)
            else:
                yaml.safe_dump(obj,file,sort_keys=sort_keys)
        if outputPath.endswith('.json'):
            json.dump(obj,file,indent=indent)
