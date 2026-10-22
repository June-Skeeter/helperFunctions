from dataclasses import dataclass, make_dataclass, field
from configparser import ConfigParser
from .dictFunctions import dictFunctions
from functools import partial
from datetime import datetime
import inspect
import os

class classMethods():

    @classmethod
    def from_dict(cls, source):  
        # Source - https://stackoverflow.com/a/55096964
        # Posted by Arne, modified by community. See post 'Timeline' for change history
        # Retrieved 2025-11-21, License - CC BY-SA 4.0  
        # Modified to accept __classmethod_flag__
        if not hasattr(cls,'__classmethod_flag__'):
            cls.__classmethod_flag__ = {'method':'from_dict','source':source}
        out = cls(**{
            k: v for k, v in source.items() 
            if k in inspect.signature(cls).parameters
        })
        return(out)
        
    @classmethod
    def from_yaml(cls,fpath,kwargs={},preserveComments=False):
        source = dictFunctions.loadDict(None,fileName=fpath,preserveComments=preserveComments)
        cls.__classmethod_flag__ = {'method':'from_yaml','source':source,'fpath':fpath}
        out = cls.from_dict(kwargs|source)
        return(out)



def fieldBuilder(name,base):
    def getSec(base,name):
        if type(base) is ConfigParser:
            return(dict(base[name]))

        return(base[name])

    value = partial(getSec,base=base,name=name)
    if value() is not None:
        if not name.startswith('date'):
            typ = type(value())
        else:
            typ = type(datetime.now())
        if typ not in [dict,list]:  
            return (name,type(value()),value())
        else:
            return (name,type(value()),field(default_factory=value))            
    else:
        return (name)

def dataclassFromYaml(filePath,bases=(),asDataclass=True,namespace=None):
    config = dictFunctions.loadDict(None,filePath,safe=True)
    className = os.path.split(filePath)[-1].replace('.yml','')
    if not asDataclass: return(config)
    dc = make_dataclass(
        className,
        [fieldBuilder(fld,config) for fld in config.keys()],
        bases=bases,
        namespace=namespace,
        kw_only=True
    )
    return dc


def fromIniDefault(filePath,bases=(),asDataclass=True,namespace=None):
    config = ConfigParser()
    config.read(filePath)
    className = os.path.split(filePath)[-1].rsplit('.',1)[0]
    if not asDataclass: return(config)
    dc = make_dataclass(
        className,
        [fieldBuilder(fld,config) for fld in config.sections()],
        bases=bases,
        namespace=namespace,
        kw_only=True
    )
    return dc