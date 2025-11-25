import dataclasses
import inspect
from dataclasses import dataclass, field, MISSING
from typing import Iterable
# from .parseCoordinates import parseCoordinates
from .dictFuncs import dcToDict,loadDict,saveDict
from datetime import datetime, timezone
import dateparser
from inspect import currentframe
from .log import log
import os

# baseClass is a parent dataclass which gives enhanced functionality to dataclasses
# * Supports type checking
# * Reading and writing from yaml files (with type checking)

@dataclass
class baseClass:
    verbose: bool = field(default=True,repr=False) # Enable verbose output for type coercion warnings
    configFile: str = field(default=None,repr=False) # If valid yaml file path is provided, the dataclass will read from the file
    typeCheck: bool = field(default=True,repr=False)
    message: str = field(default='',repr=False)
    logFile: str = field(default=f"Log file: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",repr=False)
    preserveInheritedMetadata: bool = field(default=True,repr=False)


    @classmethod
    def from_dict(cls, env):  
        # Source - https://stackoverflow.com/a/55096964
        # Posted by Arne, modified by community. See post 'Timeline' for change history
        # Retrieved 2025-11-21, License - CC BY-SA 4.0    
        return cls(**{
            k: v for k, v in env.items() 
            if k in inspect.signature(cls).parameters
        })

    def __post_init__(self,debug=False):
        if self.typeCheck:
            for (name, field) in self.__dataclass_fields__.items():
                value = getattr(self, name, None)
                self.typeEnforcement(name,value,field)
                self.checkMetadata(name,value,field)
        if self.configFile:
            self.loadFromConfigFile()
            
    def typeEnforcement(self,name,value,field):
        field_type = field.type
        if not isinstance(value, field_type) and value is not None:
            current_type = type(value)
            if self.verbose:
                self.logWarning(f"\nType mismatch for field: `{name}`\nExpected input of {field_type.__name__}, received input of {current_type.__name__}\nAttempting to coerce value: {value}",hold=True)
            if field_type == datetime:
                # self.logWarning('Auto parsing date, will assume format: YMD order and UTC time (unless specified)')
                TIMESTAMP = dateparser.parse(value,settings={'DATE_ORDER':'YMD',
                                    'RETURN_AS_TIMEZONE_AWARE':True})
                setattr(self, name, TIMESTAMP)
                self.logWarning(f'Confirm variable coerced correctly: {value}')
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
        if self.preserveInheritedMetadata:
            # Ensure metadata are not overwrittent 
            middleClasses = [mc for mc in type(self).__mro__[1:-2]]
            for mc in middleClasses:
                for key in mc.__annotations__.keys():
                    if type(self.__dataclass_fields__[name].metadata).__name__ == 'mappingproxy':
                        self.__dataclass_fields__[key].metadata = mc.__dataclass_fields__[key].metadata
        if 'options' in field.metadata:
            if isinstance(field.metadata['options'],Iterable):
                pass
                # self.logMessage('Consider implementing options enforcement for Iterable')
                # if value not in field.metadata['options']:
                #     breakpoint()
                #     self.logWarning(f"{value} is not valid")
                #     self.logError(msg=f'{name} must be one of {field.metadata["options"]}')
            else:
                if value != field.metadata['options']:
                    self.logError(msg=f'{name} must be {field.metadata["options"]}')

    def loadFromConfigFile(self):
        defaultOverwrites = [
            'dateModified'
        ]
        root,fn = os.path.split(self.configFile)
        if os.path.exists(self.configFile):
            self.logMessage(f'Loading: {self.configFile}')
            tmp,self.header = loadDict(fileName=self.configFile,returnHeader=True)
            for key,value in tmp.items():
                # Overwrite defaults
                if key not in self.__dict__.keys():
                    self.logError('Does not accept generic undefined parameters, must edit source code')
                elif (
                    self.__dict__[key] == self.__dataclass_fields__[key].default or (
                        self.__dataclass_fields__[key].default_factory is not MISSING and 
                        self.__dict__[key] == self.__dataclass_fields__[key].default_factory())
                    ):
                    setattr(self,key,value)
                elif self.__dict__[key] != value and key not in defaultOverwrites:
                    if isinstance(self.__dict__[key], Iterable):
                        pass
                        # self.logWarning(f'User input for {key} may differ from what already exists in {self.configFile}.  Confirm correct parameters.')
                    else:
                        self.logChoice(f'User input for {key}:{self.__dict__[key]} does not match the configuration in \n{self.configFile}\n proceeding will overwrite ')
        elif os.path.isdir(root) and os.listdir(root) != []:
            self.logError(f'Root path {root} exists amd is not empty but is missing {fn}. Please check.')

    def saveConfigFile(self,repr=True,inheritance=True):
        self.logMessage(f"Saving: {self.configFile}")
        if repr: keys = list(self.__annotations__.keys())
        else: keys = list(self.__dataclass_fields__.keys())
        if hasattr(self,'header'):
            header=self.header
        else:
            header=None
        saveDict(
            dcToDict(self,repr=repr,inheritance=inheritance),
            fileName=self.configFile,
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
        return(out)

    def logWarning(self,msg='',hold=False,traceback=False,verbose=None):
        if verbose is None:
            verbose = self.verbose
        if hold == True:
            self.message = '\n'.join([self.message, msg])
            out = None
        else:
            self.message = '\n'.join([self.message, msg])
            out = log(msg=f'\n\n{"*"*10} Warning {"*"*10}\n{self.message}\n',traceback=traceback,cf=currentframe(),verbose=verbose)
            self.message = ''
            self.updateLog(out)
        return(out)

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
        return(out)

    def logMessage(self,msg,verbose=None,traceback=False):
        if verbose is None:
            verbose = self.verbose
        out = log(f"\n{msg}\n",traceback=traceback,verbose=verbose,cf=currentframe())
        self.updateLog(out)
        return(out)

    def updateLog(self,out):
        self.logFile=self.logFile+'\n\n'+out
