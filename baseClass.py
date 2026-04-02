import os
import inspect
import dataclasses
from types import MappingProxyType
from dataclasses import dataclass, field, MISSING, make_dataclass
from .parseCoordinates import parseCoordinates
from typing import Iterable, Callable
from .dictFuncs import dictFuncs
from datetime import datetime, timezone
import dateparser
from inspect import currentframe
from .log import log

# from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from zoneinfo import ZoneInfo


# ruamel = YAML()
# @dataclass
class spatialObject:

    def __init__(self,lat_lon):
        if isinstance(lat_lon,list) and len(lat_lon) == 2:
            if type(lat_lon[0]) is float and type(lat_lon[1]) is float:
                self.lat_lon = lat_lon
            else:
                lat,lon=lat_lon[0],lat_lon[1]
                self.parse(lat,lon)
        elif isinstance(lat_lon,str) and ',' in lat_lon:
            lat,lon=lat_lon.split(',')
            self.parse(lat,lon)
        elif lat_lon is not None:
            breakpoint()
            self.lat_lon = f'Could not parse {lat_lon}'
        else:
            self.lat_lon = None
    

    def parse(self,lat,lon):
        pC = parseCoordinates(latitude=lat,longitude=lon)
        self.lat_lon = [pC.latitude, pC.longitude]

# baseClass is a parent dataclass which gives enhanced functionality to dataclasses
# * Supports type checking
# * Reading and writing from yaml files (with type checking)
class baseClassMethods(dictFuncs):

    @classmethod
    def requiredArgs(cls):
        return([k for k,v in inspect.signature(cls.__init__).parameters.items() if v.default is v.empty and k != 'self'])

    @classmethod
    def from_class(cls,env,kwargs):
        return(cls(**{k:getattr(env,k) for k,v in cls.__dataclass_fields__.items() if hasattr(env,k) and v.init}|kwargs))

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
        if kwargOverwrite:
            env = cls.loadDict(None,fileName=fpath)|kwargs
        else:
            env = kwargs|cls.loadDict(None,fileName=fpath)
        return(cls.from_dict(env))

    @classmethod
    def metadataMap(cls,description,options=None):
        # Streamline the creation of metadata in dataclass fields by formatting a standardized dict
        out = {'description':description}
        if options is not None:
            out['options'] = options
        return(out)
    
    @classmethod
    def template(cls,kwargs={}):
        signature = inspect.signature(cls.__init__)
        for param in signature.parameters.values():
            if param.name not in ['self'] and param.default is param.empty:
                kwargs[param.name] = param.name
        #hiddenDefaults implicit to baseclass
        kwargs = kwargs | {'typeCheck':False,'readOnly':True,'fromFile':False}
        template = cls.from_dict(kwargs)
        templateFilePath = 'template. config FilePath'
        template = template.to_dict()
        data = CommentedMap()
        for key,value in template.items():
            data[key] = value
            fld = cls.__dataclass_fields__[key]
            comment = f'type={fld.type.__name__};metadata={fld.metadata}'
            if fld.default is not MISSING:
                if fld.type is str and fld.default is not None:
                    comment = comment +f';default="{fld.default}"'
                else:
                    comment = comment +f';default={fld.default}'
            elif fld.default_factory is not MISSING:
                if callable(fld.default_factory):
                    comment = comment +f';default_factory={fld.default_factory()}'                    
                else:
                    comment = comment +f';default_factory={fld.default_factory}'
            data.yaml_add_eol_comment(comment,key=key)
        cls.saveDict(data,templateFilePath,header=cls.__dataclass_fields__['header'].default)
        return(templateFilePath)
        
    @classmethod
    def fromTemplate(cls,template,base=None):
        tmp = cls.loadDict(fileName=template)
        flds = []
        for key in tmp.ca.items.keys():
            cmt = (';'.join([c.value.strip('# ').rstrip('\n') for c in tmp.ca.items[key] if c is not None])).split(';')
            cmt = {c.split('=')[0]: eval(c.split('=')[-1]) for c in cmt}
            if 'default' in cmt:
                flds.append((key,cmt['type'],field(default=cmt['default'],metadata=cmt['metadata'])))
            elif 'default_factory' in cmt:
                flds.append((key,cmt['type'],field(default_factory=cmt['default_factory'],metadata=cmt['metadata'])))
            else:
                flds.append((key,cmt['type'],field(metadata=cmt['metadata'])))

            
        Name = os.path.split(template)[-1].replace('.yml','')
        if base is None:
            base = (baseClassMethods,)
        return(make_dataclass(Name,flds,bases=base,kw_only=True))

class baseFunctions(baseClassMethods):
    
    def logError(self,msg='',traceback=True,kill=True,verbose=None):
        if verbose is None:
            verbose = self.verbose
        out = log(msg=f'\n\n{"*"*11} Error {"*"*11}\n{msg}\n{"*"*10} Exiting {"*"*10}\n',traceback=traceback,kill=kill,cf=currentframe(),verbose=verbose)

    def logWarning(self,msg='',hold=False,traceback=False,verbose=None):
        if verbose is None:
            verbose = self.verbose
        if not hasattr(self,'message') or self.message == '':
            self.message = msg
        else:
            self.message = '\n'.join([self.message, msg])
        if not hold:
            out = log(msg=f'{"*"*10} Warning {"*"*10}\n{self.message}\n',traceback=traceback,cf=currentframe(),verbose=verbose)
            self.message = ''

    def logChoice(self,msg,proceed='Y',kill=False):
        out = log(msg=msg,cf=currentframe(),verbose=True)
        i = input(f'Enter {proceed} to continue or any other key to exit: ')
        if i == proceed:
            return (True)
        elif kill:
            log(msg='Exiting',kill=kill)
        else:
            return (False)

    def logMessage(self,msg,verbose=None,traceback=False):
        if verbose is None:
            verbose = self.verbose
        out = log(f"{msg}",traceback=traceback,verbose=verbose,cf=currentframe())

    def currentTimeString(self=None,fmt='%Y-%m-%dT%H:%M:%SZ'):
        return(datetime.now(timezone.utc).strftime(fmt))
    
    def coerceType(self,name,dtype,value,default=None):
        # Simple cases
        if dtype in [bool,str,int,float]:
            setattr(self,name,dtype(value))
        # Custom for datetimes
        elif dtype is datetime:
            self.parseDatetime(name,value)
        # Custom spatial data
        elif dtype is spatialObject:
            setattr(self,name,spatialObject(value).lat_lon)
        # Custom for nested dataclasses with dict inputs
        elif dataclasses.is_dataclass(default) and isinstance(value,dict):
            setattr(self,name,default(**value))
        else:
            self.logMessage(f'More complex type, add method to handle: {name, dtype,value}')
            breakpoint()

    def parseDatetime(self,name,value):
        if hasattr(self,'timezone'):
            kwargs = {'DATE_ORDER':'YMD','RETURN_AS_TIMEZONE_AWARE':True,'TIMEZONE':str(ZoneInfo(getattr(self,'timezone')))}
        else:
            kwargs = {'DATE_ORDER':'YMD','RETURN_AS_TIMEZONE_AWARE':False}
        self.logWarning(f'The datetime object {name}:{value} will be parsed as with: {kwargs}',hold=True)
        setattr(self,name,dateparser.parse(value,settings=kwargs))
        self.logWarning(f'Confirm variable coerced correctly: {getattr(self,name)}')


mdMap = baseClassMethods.metadataMap

@dataclass
class baseDataClass(baseFunctions):
    # verbose: bool = False
    verbose: bool = field(default=True,repr=False) # Enable verbose output for type coercion warnings
    typeEnforce: bool = field(default=True,repr=False) # Enable type enforcement
    typeCoercion: bool = field(default=True,repr=False) # Enable type coercion if fails type check
    optionEnforce: bool = field(default=True,repr=False)

    def __post_init__(self):
        fields = self.__dataclass_fields__
        if self.typeEnforce:
            self.checkType(fields,coerce=self.typeCoercion)
        if self.optionEnforce:
            self.checkOptions(fields)

    def checkType(self,fieldValues,coerce=False):
        # Dump fields to tuple (name,dtype,value,default) for if they fail checks
        attributes = [
            (key,value.type,getattr(self,key,None),value.default if value.default is not MISSING else value.default_factory)
            for key,value in fieldValues.items() if not any(
                [getattr(self,key,None) is None, # None's pass
                inspect.isclass(value.type) and isinstance(getattr(self,key,None),value.type), # Matching types pass 
                value.type is callable and (getattr(self,key,None) is callable or dataclasses.is_dataclass(getattr(self,key,None))) # Callables pass (in some cases)
                ])]
        for name,dtype,value,default in attributes:
            if coerce:
                self.coerceType(name,dtype,value,default)
            elif not coerce:
                self.logError(f'Type check failed: {name} of type {dtype}',traceback=True)

    def checkOptions(self,fields):
        # Dump fields to tuple (name,dtype,value,default) for if they fail checks
        attributes = [
            (key,getattr(self,key),value['options']) for key,value in fields.items() if not any(
                [getattr(self,key) is None, # None's pass
                'options' not in value.metadata, # Has no options
                'options' in value.metadata and getattr(self,key) in value.metadata['options'], # Has options which are satisfied
                ])]
        if len(attributes) == 0:
            return
        for name,value,options in attributes:
            self.logMessage(f'{name}: {value} is invalid, must be one of {options}')
        self.logError('Update parameters to meet required options')

    def to_dict(self,repr=True,inheritance=True,keepNull=True,sorted=False,onlyID=False,debug=False):
        if onlyID == True:
            data = {key:self.__dict__[key] for key in self.requiredArgs()} 
        else:
            data = dictFuncs().dcToDict(self,repr=repr,inheritance=inheritance,keepNull=keepNull,sorted=sorted)
        return(data)

    def saveConfigFile(self,configFilePath,repr=True,inheritance=True,keepNull=True,sorted=True,debug=False):
        self.lastModified = self.currentTimeString()
        configDict = self.to_dict(repr=repr,inheritance=inheritance,keepNull=keepNull,sorted=sorted,debug=debug)
        if hasattr(self,'header') and self.header is not None:
            header=self.header
        else:
            header=None
        try:
            self.saveDict(configDict,fileName=configFilePath,header=header)
        except:
            breakpoint()
