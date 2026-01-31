import os
import inspect
import dataclasses
from types import MappingProxyType
from dataclasses import dataclass, field, MISSING
from typing import Iterable, Callable
# from .parseCoordinates import parseCoordinates
from .dictFuncs import dcToDict,saveDict,loadDict
from datetime import datetime, timezone
# import dateparser
from inspect import currentframe
from .log import log

# def f:
#     return(loadDict)

# baseClass is a parent dataclass which gives enhanced functionality to dataclasses
# * Supports type checking
# * Reading and writing from yaml files (with type checking)
@dataclass
class baseClass:
    UID: str = field(default=None,repr=False)
    verbose: bool = field(default=False,repr=False) # Enable verbose output for type coercion warnings

    typeCheck: bool = field(default=True,repr=False)
    message: str = field(default='',repr=False)
    logFile: str = field(default=f"Log file: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n",repr=False)
    # keepNull: bool = field(default=True,repr=False)

    debug: bool = field(default=False,repr=False)
    
    fromFile: bool = field(default=False,repr=False) # set to true to load from config file (if exists)

    configReset: bool = field(default=False,repr=False)
    configFileExists: bool = field(default=False,repr=False)
    configFilePath: str = field(default=None,repr=False)

    readOnly: bool = field(default=True,repr=False) # Only write config if readOnly == False or configFileExists=False

    lastModified: str = field(default=None,repr=False)
    
    _inheritedMetadata: bool = field(default=True,repr=False)

    loadDict: Callable = field(default_factory=lambda: loadDict, repr=False)
    saveDict: Callable = field(default_factory=lambda: saveDict, repr=False)

    def __post_init__(self):
        if type(self).__name__ != 'baseClass':
            if self.fromFile and os.path.exists(self.configFilePath) and not self.configReset:
                self.loadFromConfigFile()
                self.configFileExists = True
            self.logMessage(f"Running: {type(self)}")
            if self.typeCheck:
                self.inspectFields()

    def close(self):
        if not self.readOnly or not self.configFileExists:
            self.saveConfigFile()
        return (self.logFile)
        
    def inspectFields(self):
        for (name, field) in self.__dataclass_fields__.items():
            value = getattr(self, name, None)
            self.typeEnforcement(name,value,field)
            self.checkMetadata(name,value,field)
            
    def typeEnforcement(self,name,value,field):
        field_type = field.type
        if not isinstance(value, field_type) and value is not None:
            current_type = type(value)
            self.logWarning(f"\nType mismatch for field: `{name}`\nExpected input of {field_type.__name__}, received input of {current_type.__name__}\nAttempting to coerce value: {value}",hold=True)
            if dataclasses.is_dataclass(value) and hasattr(value,'to_dict'):
                setattr(self,name,value.to_dict())               
            elif hasattr(field_type, '__module__') and field_type.__module__ == 'builtins':
                try:
                    if type(value) is str and field_type is list:
                        setattr(self,name,[value])
                    else:
                        setattr(self, name,  field_type(value))
                    if not current_type is int and not field_type is float:
                        self.logWarning(f'Confirm variable coerced correctly: {value}')
                except:
                    self.logError(f"The field `{name}` was assigned by `{current_type.__name__}` instead of `{field_type.__name__}` and could not be coerced to required type.")
            elif dataclasses.is_dataclass(self.__dataclass_fields__[name].default_factory):
                self.logMessage(f'Parsing nested dataclass: {name}')
                setattr(self,name,self.__dataclass_fields__[name].default_factory(**value))
            elif self.verbose:
                self.logError(f'Coercion failed for {name} \nCannot coerce custom type: {field_type}')
    
    def checkMetadata(self,name,value,field):
        if self._inheritedMetadata:
            # Ensure metadata are not overwritten 
            if not field.metadata:
                middleClasses = [mc for mc in type(self).__mro__[1:-2]]
                for mc in middleClasses:
                    if name in mc.__annotations__.keys():
                        self.__dataclass_fields__[name].metadata = mc.__dataclass_fields__[name].metadata
            elif hasattr(self,'defaultMD'):
                md = dict(field.metadata)
                for k,v in self.defaultMD.items():
                    if k not in md.keys():
                        md[k] = v
                self.__dataclass_fields__[name].metadata = MappingProxyType(md)
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
                    self.logChoice('Proceed with interactive debug session')
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
        if self.debug and 'traceMetadata' in self.__dict__.keys():
            print(self.__dict__['traceMetadata'])
            breakpoint()
        
    def to_dict(self,repr=True,inheritance=True,keepNull=True,majorOrder=1,minorOrder=1):
        return(dcToDict(self,repr=repr,inheritance=inheritance,keepNull=keepNull,majorOrder=majorOrder,minorOrder=minorOrder))

    def saveConfigFile(self,repr=True,inheritance=True,keepNull=True,verbose=None,majorOrder=1,minorOrder=1):
        self.lastModified = self.modTime()
        if verbose is None:
            verbose = self.verbose
        configDict = self.to_dict(repr=repr,inheritance=inheritance,keepNull=keepNull,majorOrder=majorOrder,minorOrder=minorOrder)
        if not self.configFilePath:
            self.logMessage('No filepath provided, only returning config dictionary')
        else:
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


    def logChoice(self,msg,proceed='Y',verbose=None):
        # if verbose is None:
        #     verbose = self.verbose
        out = log(msg=msg,cf=currentframe(),verbose=True)
        i = input(f'Enter {proceed} to continue or any other key to exit: ')
        if i == proceed:
            return
        else:
            log(msg='Exiting',kill=True)
        self.updateLog(out)


    def logMessage(self,msg,verbose=None,traceback=False):
        if verbose is None:
            verbose = self.verbose
        # if not verbose:
        #     breakpoint()
        out = log(f"{msg}\n",traceback=traceback,verbose=verbose,cf=currentframe())
        self.updateLog(out)


    def updateLog(self,out):
        if out.startswith('Log file: '):
            out = out.split('\n',1)[-1]
        self.logFile=self.logFile+'\n'+out

    def modTime(self):
        return(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))

    @classmethod
    def from_class(cls,env,kwargs):
        return(cls(**{k:getattr(env,k) for k,v in cls.__dataclass_fields__.items() if hasattr(env,k) and v.init}|kwargs))



    @classmethod
    def from_dict(cls, env):  
        # Source - https://stackoverflow.com/a/55096964
        # Posted by Arne, modified by community. See post 'Timeline' for change history
        # Retrieved 2025-11-21, License - CC BY-SA 4.0    
        return cls(**{
            k: v for k, v in env.items() 
            if k in inspect.signature(cls).parameters
        })
    
    @classmethod
    def template(cls):
        template = {}
        hidden = {'typeCheck':False}
        for k,v in cls.__dataclass_fields__.items():
            if v.repr:
                desc = f'# datatype={v.type.__name__}; '
                for key,value in v.metadata.items():
                    desc = desc + f"{key}={v.metadata[key]}; "
                template[k] = desc
            else:            
                hidden[k] = ''
        template = cls.from_dict(template|hidden).to_dict()
        return(template)