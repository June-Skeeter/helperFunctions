import os
import inspect
import dataclasses
from types import MappingProxyType
from dataclasses import dataclass, field, MISSING, make_dataclass
from .parseCoordinates import parseCoordinates
from typing import Iterable, Callable
from .dictFuncs import dcToDict,saveDict,loadDict,unpackDict
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
        pC = parseCoordinates(UID=None,latitude=lat,longitude=lon)
        self.lat_lon = [pC.latitude, pC.longitude]

# baseClass is a parent dataclass which gives enhanced functionality to dataclasses
# * Supports type checking
# * Reading and writing from yaml files (with type checking)
@dataclass
class baseClass:
    UID: str = field(default=None,repr=False)
    verbose: bool = field(default=True,repr=False) # Enable verbose output for type coercion warnings

    typeCheck: bool = field(default=True,repr=False)
    message: str = field(default='',repr=False)
    logFile: str = field(default=f"Log file: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n",repr=False)

    debug: bool = field(default=False,repr=False)
    
    fromFile: bool = field(default=False,repr=False) # set to true to load from config file (if exists)

    # configReset: bool = field(default=False,repr=False)
    configFileExists: bool = field(default=False,repr=False)
    configFilePath: str = field(default=None,repr=False)

    readOnly: bool = field(default=True,repr=False) # Only write config if readOnly == False or configFileExists=False

    loadDict: Callable = field(default_factory=lambda: loadDict, repr=False, init=False)
    saveDict: Callable = field(default_factory=lambda: saveDict, repr=False, init=False)
    unpackDict: Callable = field(default_factory=lambda: unpackDict, repr=False, init=False)

    def __post_init__(self):
        if type(self).__name__ != 'baseClass':
            if self.fromFile and self.configFilePath is not None:
                if os.path.exists(self.configFilePath):
                    self.loadFromConfigFile()
                    self.configFileExists = True
            if self.debug:
                self.logMessage(f"Running: {type(self)}")
            if self.typeCheck:
                self.inspectFields()
                
    # def formatUID(self,UID=None):
    #     self.logMessage('Formatting UID?')
    #     if self.UID is None:
    #         if self.UID_link is None:
    #             self.UID_link = UID
    #         self.UID = getattr(self,self.UID_link)
    #     if '_' not in self.UID or not self.UID.split('_')[-1].isnumeric():
    #         self.UID = self.UID + '_1'

    # def updateUID(self):
    #     if '_' in self.UID and self.UID.split('_')[-1].isnumeric():
    #         index = int(self.UID.split('_')[-1])+1
    #         self.UID = self.UID.rsplit('_',1)[0]+'_'+str(index)
    #     else:
    #         self.formatUID()
    #     if self.UID_link is not None:
    #         setattr(self,self.UID_link,self.UID)

    def inspectFields(self):
        for (name, field) in self.__dataclass_fields__.items():
            value = getattr(self, name, None)
            self.typeEnforcement(name,value,field)
            self.checkMetadata(name,value,field)
            
    def typeEnforcement(self,name,value,field):
        field_type = field.type
        if not isinstance(value, field_type) and value is not None:
            current_type = type(value)
            if field_type is datetime:
                if hasattr(self,'timezone'):
                    kwargs = {'DATE_ORDER':'YMD','RETURN_AS_TIMEZONE_AWARE':True,'TIMEZONE':str(ZoneInfo(self.timezone))}
                else:
                    kwargs = {'DATE_ORDER':'YMD','RETURN_AS_TIMEZONE_AWARE':False}
                self.logWarning(f'The datetime object {name}:{value} will be parsed as with: {kwargs}',hold=True)
                setattr(self,name,dateparser.parse(value,settings=kwargs))
                self.logWarning(f'Confirm variable coerced correctly: {getattr(self,name)}')
            elif field_type is spatialObject:
                setattr(self,name,spatialObject(value).lat_lon)
            elif dataclasses.is_dataclass(value) and hasattr(value,'to_dict'):
                setattr(self,name,value.to_dict())     
            elif hasattr(field_type, '__module__') and field_type.__module__ == 'builtins':
                self.logWarning(f"\nType mismatch for field: `{name}`\nExpected input of {field_type.__name__}, received input of {current_type.__name__}\nAttempting to coerce value: {value}",hold=True)
                try:
                    if isinstance(value,str) and field_type is list:
                        setattr(self,name,[value])
                    else:
                        setattr(self, name,  field_type(value))
                    if not isinstance(current_type,int) and not field_type is float:
                        self.logWarning(f'Confirm variable coerced correctly: {value}')
                except:
                    self.logError(f"The field `{name}` was assigned by `{current_type.__name__}` instead of `{field_type.__name__}` and could not be coerced to required type.")
            elif dataclasses.is_dataclass(self.__dataclass_fields__[name].default_factory):
                self.logMessage(f'Parsing nested dataclass: {name}, is this assumption too complicated?')
                breakpoint()
                setattr(self,name,self.__dataclass_fields__[name].default_factory(**value))
            elif self.verbose:
                self.logError(f'Coercion failed for {name} \nCannot coerce custom type: {field_type}')
    
    def checkMetadata(self,name,value,field):
        if 'options' in field.metadata:
            if isinstance(field.metadata['options'],Iterable):
                if value in field.metadata['options']:
                    pass
                elif field.type is str and value not in field.metadata['options'] and value is not None:
                    self.logWarning(msg=f"{value} is not valid")
                    breakpoint()
                    self.logError(msg=f'{name} must be one of {field.metadata["options"]}')

                elif value is not None:
                    self.logWarning('Options currently only enabled for string types')
                    if self.logChoice('Proceed with interactive debug session'):
                        breakpoint()
            else:
                if value != field.metadata['options']:
                    self.logError(msg=f'{name} must be {field.metadata["options"]}')

    def loadFromConfigFile(self):
        defaultOverwrites = [
            'dateModified'
        ]
        self.logMessage(f"Reading: {self.configFilePath}")
        tmp,self.header = self.loadDict(fileName=self.configFilePath,returnHeader=True)
        for key,value in tmp.items():
            # Overwrite defaults
            if key not in self.__dataclass_fields__.keys():
                self.logError(f'Does not accept generic undefined parameters,\n {key} field must be added to source code')
                breakpoint()
            elif key in defaultOverwrites:
                setattr(self,key,value)
            elif key not in self.__dict__.keys():
                setattr(self,key,value)
            elif value != self.__dict__[key]:
                if (self.__dataclass_fields__[key].default == self.__dict__[key] or 
                    (self.__dataclass_fields__[key].default_factory is not MISSING and self.__dataclass_fields__[key].default_factory() == self.__dict__[key])):
                    setattr(self,key,value)
                else:
                    if self.readOnly:
                        self.logWarning('Cannot over-write yaml configurations with field inputs when running with readOnly = True')
                    else:
                        self.logWarning(f'Overwriting value in {key}')

        
    def to_dict(self,repr=True,inheritance=True,keepNull=True,sorted=False):
        return(dcToDict(self,repr=repr,inheritance=inheritance,keepNull=keepNull,sorted=sorted))

    def saveConfigFile(self,repr=True,inheritance=True,keepNull=True,verbose=None,sorted=True):
        self.lastModified = self.currentTimeString()
        if verbose is None:
            verbose = self.verbose
        configDict = self.to_dict(repr=repr,inheritance=inheritance,keepNull=keepNull,sorted=sorted)
        if not self.configFilePath:
            self.logError('No configFilePath provided')
        elif not self.readOnly:
            self.logMessage(f"Saving: {self.configFilePath}")
            if hasattr(self,'header') and self.header is not None:
                header=self.header
            else:
                header=None
            self.saveDict(
                configDict,
                fileName=self.configFilePath,
                header=header
                )
        else:
            self.logMessage(f'readOnly={self.readOnly}, not saving {self.configFilePath}')

    def logError(self,msg='',traceback=True,kill=True,verbose=None):
        if verbose is None:
            verbose = self.verbose
        out = log(msg=f'\n\n{"*"*11} Error {"*"*11}\n{msg}\n{"*"*10} Exiting {"*"*10}\n',traceback=traceback,kill=kill,cf=currentframe(),verbose=verbose)
        self.updateLog(out)

    def logWarning(self,msg='',hold=False,traceback=False,verbose=None):
        if verbose is None:
            verbose = self.verbose
        if self.message == '':
            self.message = msg
        else:
            self.message = '\n'.join([self.message, msg])
        if not hold:
            out = log(msg=f'{"*"*10} Warning {"*"*10}\n{self.message}\n',traceback=traceback,cf=currentframe(),verbose=verbose)
            self.message = ''
            self.updateLog(out)


    def logChoice(self,msg,proceed='Y',kill=False):
        out = log(msg=msg,cf=currentframe(),verbose=True)
        self.updateLog(out)
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
        out = log(f"{msg}\n",traceback=traceback,verbose=verbose,cf=currentframe())
        self.updateLog(out)


    def updateLog(self,out):
        if out.startswith('Log file: '):
            out = out.split('\n',1)[-1]
        self.logFile=self.logFile+'\n'+out

    def currentTimeString(self=None,fmt='%Y-%m-%dT%H:%M:%SZ'):
        return(datetime.now(timezone.utc).strftime(fmt))
    
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
            env = {'readOnly':True}|loadDict(fileName=fpath)|kwargs
        else:
            env = kwargs|loadDict(fileName=fpath)|{'readOnly':True}
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
        templateFilePath = template.configFilePath
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
        saveDict(data,templateFilePath,header=cls.__dataclass_fields__['header'].default)
        return(templateFilePath)
        
    @classmethod
    def fromTemplate(cls,template,base=None):
        tmp = loadDict(fileName=template)
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
            base = (baseClass,)
        return(make_dataclass(Name,flds,bases=base,kw_only=True))
