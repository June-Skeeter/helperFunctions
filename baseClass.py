import os
import inspect
import dataclasses
from types import MappingProxyType
from dataclasses import dataclass, field, MISSING
from typing import Iterable
# from .parseCoordinates import parseCoordinates
from .dictFuncs import dcToDict,loadDict,saveDict
from datetime import datetime, timezone
import dateparser
from inspect import currentframe
from .log import log

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
    keepNull: bool = field(default=True,repr=False)

    configFilePath: str = field(default=None,repr=False) # If valid yaml file path is provided, the dataclass will read from the file
    configFileRoot: str = field(default=None,repr=False) # If valid yaml file path is provided, the dataclass will read from the file
    configFileName: str = field(default=None,repr=False) # If valid yaml file path is provided, the dataclass will read from the file
    configFileExtension: str = field(default='.yml',repr=False)
    configFileExists: bool = field(default=True,repr=False)

    safeMode: bool = field(default=True,repr=False) # Only write config if safemode == False or configFileExists=False

    # defaultMD: dict = field(default_factory=lambda:{'optional':True},init=False,repr=False)
    
    _inheritedMetadata: bool = field(default=True,repr=False)

    @classmethod
    def from_dict(cls, env):  
        # Source - https://stackoverflow.com/a/55096964
        # Posted by Arne, modified by community. See post 'Timeline' for change history
        # Retrieved 2025-11-21, License - CC BY-SA 4.0    
        return cls(**{
            k: v for k, v in env.items() 
            if k in inspect.signature(cls).parameters
        })

    def __post_init__(self):
        if type(self).__name__ != 'baseClass':
            self.logMessage(f"Running: {type(self)}")
            if self.configFilePath is None and (
                self.configFileRoot is not None and self.configFileName is not None):
                if '.' not in self.configFileName:
                    self.configFileName = self.configFileName+self.configFileExtension
                self.configFilePath = os.path.join(self.configFileRoot,self.configFileName)
            if self.configFilePath:
                self.loadFromConfigFile()
            else:
                self.configFileExists = False
            if self.typeCheck:
                self.inspectFields()

        
    def close(self):
        if not self.safeMode or not self.configFileExists:
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
            if field_type == datetime:
                # self.logWarning('Auto parsing date, will assume format: YMD order and UTC time (unless specified)')
                TIMESTAMP = dateparser.parse(value,settings={'DATE_ORDER':'YMD','RETURN_AS_TIMEZONE_AWARE':True})
                setattr(self, name, TIMESTAMP)
                self.logWarning(f'Confirm variable coerced correctly: {value}')
            elif dataclasses.is_dataclass(value) and hasattr(value,'to_dict'):
                setattr(self,name,value.to_dict())               
            elif hasattr(field_type, '__module__') and field_type.__module__ == 'builtins':
                try:
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
                    self.logWarning(f"{value} is not valid")
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
        if self.configFileRoot is None and self.configFileName is None:
            self.configFileRoot, self.configFileName = os.path.split(self.configFilePath)
        if os.path.exists(self.configFilePath):
            self.logMessage(f"Reading: {self.configFilePath}")
            tmp,self.header = loadDict(fileName=self.configFilePath,returnHeader=True)
            for key,value in tmp.items():
                # Overwrite defaults
                if key not in self.__dataclass_fields__.keys():
                    self.logError(f'Does not accept generic undefined parameters, field {key} must be added to source code')
                elif key in defaultOverwrites:
                    setattr(self,key,value)
                elif key not in self.__dict__.keys():
                    setattr(self,key,value)
                elif value != self.__dict__[key]:
                    if (self.__dataclass_fields__[key].default == self.__dict__[key] or 
                        (self.__dataclass_fields__[key].default_factory is not MISSING and self.__dataclass_fields__[key].default_factory() == self.__dict__[key])):
                        setattr(self,key,value)
                    else:
                        if self.safeMode:
                            self.logWarning('Cannot over-write yaml configurations with field inputs when running with safeMode = True')
                        else:
                            self.logWarning(f'typeChecking issue when reading from yaml')
                            self.logChoice('Proceed with interactive debug session')
                            breakpoint()
            self.configFileExists = True
        else:
            self.configFileExists = False
        
    def to_dict(self,repr=True,inheritance=True,keepNull=None,majorOrder=1,minorOrder=1):
        if keepNull is None:
            keepNull = self.keepNull
        return(dcToDict(self,repr=repr,inheritance=inheritance,keepNull=keepNull,majorOrder=majorOrder,minorOrder=minorOrder))

    def saveConfigFile(self,repr=True,inheritance=True,keepNull=True,verbose=None,majorOrder=1,minorOrder=1):
        if verbose is None:
            verbose = self.verbose
        configDict = self.to_dict(repr=repr,inheritance=inheritance,keepNull=keepNull,majorOrder=majorOrder,minorOrder=minorOrder)
        if not self.configFilePath:
            self.logMessage('No filepath provided, only returning config dictionary')
        else:
            self.logMessage(f"Saving: {self.configFilePath}")
            if hasattr(self,'header'):
                header=self.header
            else:
                header=None
            saveDict(
                configDict,
                fileName=self.configFilePath,
                header=header
            )

    def syncAttributes(self,incoming,inheritance=False,overwrite=False):
        excl = baseClass.__dataclass_fields__.keys()
        # Add attributes of one class to another and avoid circular imports
        self.logWarning(msg=f'Syncing {type(incoming).__name__} into {type(self).__name__}',traceback=True)
        if inheritance:
            keys = [k for k in list(incoming.__dict__.keys())
                    if k not in excl]
        else:
            keys = list(incoming.__annotations__.keys())
        for key in keys:
            if not hasattr(self,key):
                setattr(self,key,incoming.__dict__[key])
            elif overwrite and self.__dict__[key] != incoming.__dict__[key]:
                setattr(self,key,incoming.__dict__[key])
               

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
        if verbose is None:
            verbose = self.verbose
        out = log(msg=msg,cf=currentframe(),verbose=verbose)
        i = input(f'Enter {proceed} to continue or any other key to exit: ')
        if i == proceed:
            return
        else:
            log(msg='Exiting',kill=True)
        self.updateLog(out)


    def logMessage(self,msg,verbose=None,traceback=False):
        if verbose is None:
            verbose = self.verbose
        out = log(f"{msg}\n",traceback=traceback,verbose=verbose,cf=currentframe())
        self.updateLog(out)


    def updateLog(self,out):
        if out.startswith('Log file: '):
            out = out.split('\n',1)[-1]
        self.logFile=self.logFile+'\n'+out


    @classmethod
    def template(cls):
        template = {}
        for k,v in cls.__dataclass_fields__.items():
            if v.repr:
                desc = {'datatype':v.type.__name__,}
                if 'description' in v.metadata:
                    desc['description'] = v.metadata['description']
                if 'options' in v.metadata:
                    desc['options'] = v.metadata['options']
                template[k] = desc
        return(template)