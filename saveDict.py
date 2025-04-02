import os
import yaml
import json
# save a dict (obj) to a file (outputPath) in either .json or .yml format
def saveDict(obj,outputPath,sort_keys=False,indent=None):
    if os.path.split(outputPath)[0] == '':
        pass
    elif not os.path.isdir(os.path.split(outputPath)[0]):
        os.makedirs(os.path.split(outputPath)[0])
    with open(outputPath,'w') as file:
        if outputPath.endswith('.yml'):
            yaml.safe_dump(obj,file,sort_keys=sort_keys)
        if outputPath.endswith('.json'):
            json.dump(obj,file,indent=indent)
