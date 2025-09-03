
import os
from . import updateDict
# Stashing here incase needed for later.  
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

def packDict(itemList,format=os.path.sep,limit=None,order=-1,fill=None,verbose=False):
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
        b = key.split(format)
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
        Tree = updateDict.updateDict(Tree,subTree,overwrite='append',verbose=verbose)
    return(Tree)
