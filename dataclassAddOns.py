from dataclasses import dataclass, make_dataclass, field
from configparser import ConfigParser
from .dictFunctions import dictFunctions
from functools import partial
from datetime import datetime
import inspect
import os

class classMethods():

    @classmethod
    def from_dict(cls, env):  
        # Source - https://stackoverflow.com/a/55096964
        # Posted by Arne, modified by community. See post 'Timeline' for change history
        # Retrieved 2025-11-21, License - CC BY-SA 4.0    
        return(cls(**{
            k: v for k, v in env.items() 
            if k in inspect.signature(cls).parameters
        }))
        
    @classmethod
    def from_yaml(cls,fpath,kwargs={},kwargOverwrite=False):
        # if 'debug' in kwargs and kwargs['debug']:
        if kwargOverwrite:
            env = cls.loadDict(None,fileName=fpath)|kwargs
        else:
            env = kwargs|cls.loadDict(None,fileName=fpath)
        return(cls.from_dict(env))



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