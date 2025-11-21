import dataclasses
from dataclasses import dataclass, field, MISSING
from typing import Iterable
from .parseCoordinates import parseCoordinates
from .dictFuncs import dcToDict,loadDict,saveDict
from datetime import datetime, timezone
import dateparser
from inspect import currentframe
from .log import log
import os

# baseFunctions is a parent dataclass which gives enhanced functionality to dataclasses
# * Supports type checking
# * Reading and writing from yaml files (with type checking)

@dataclass
class baseFunctions:
    # dependencies = {}
    verbose: bool = field(default=True,repr=False) # Enable verbose output for type coercion warnings
    yamlConfigFile: str = field(default=None,repr=False) # If valid yaml file path is provided, the dataclass will read from the file
    typeCheck: bool = field(default=True,repr=False)
    message: str = field(default='',repr=False)
    logFile: str = field(default=f"Log file: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",repr=False)
    preserveInheritedMetadata: bool = field(default=False,repr=False)

    def __post_init__(self,debug=False):
        if self.yamlConfigFile:
            self.loadFromYaml()
        if not self.typeCheck:
            return
        for (name, field) in self.__dataclass_fields__.items():
            self.typeEnforcement(name,field)
            self.checkMetadata(name,field)

        
    def typeEnforcement(self,name,field):
        field_type = field.type
        if not isinstance(self.__dict__[name], field_type) and self.__dict__[name] is not None:
            current_type = type(self.__dict__[name])
            if self.verbose:
                self.logWarning(f"\nType mismatch for field: `{name}`\nExpected input of {field_type.__name__}, received input of {current_type.__name__}\nAttempting to coerce value: {self.__dict__[name]}",hold=True)
            if field_type == datetime:
                # self.logWarning('Auto parsing date, will assume format: YMD order and UTC time (unless specified)')
                TIMESTAMP = dateparser.parse(self.__dict__[name],settings={'DATE_ORDER':'YMD',
                                    'RETURN_AS_TIMEZONE_AWARE':True})
                setattr(self, name, TIMESTAMP)
                self.logWarning(f'Confirm variable coerced correctly: {self.__dict__[name]}')
            elif hasattr(field_type, '__module__') and field_type.__module__ == 'builtins':
                try:
                    if name in parseCoordinates.__annotations__.keys():
                        pC = parseCoordinates(**{name:self.__dict__[name]})
                        self.__dict__[name] = pC.__dict__[name]
                        self.logWarning(f'Confirm coordinate parsed correctly: {self.__dict__[name]}')
                    else:
                        setattr(self, name,  field_type(self.__dict__[name]))
                        if not current_type is int and not field_type is float:
                            self.logWarning(f'Confirm variable coerced correctly: {self.__dict__[name]}')
                except:
                    self.logError(f"The field `{name}` was assigned by `{current_type.__name__}` instead of `{field_type.__name__}` and could not be coerced to required type.")
            elif dataclasses.is_dataclass(self.__dataclass_fields__[name].default_factory):
                self.logMessage(f'Parsing nested dataclass: {name}')
                setattr(self,name,self.__dataclass_fields__[name].default_factory(**self.__dict__[name]))
            elif self.verbose:
                breakpoint()
                self.logError(f'Coercion failed for {name} \nCannot coerce custom type: {field_type}')
    
    def checkMetadata(self,name,field):
        if self.preserveInheritedMetadata:
            # Ensure metadata are not overwrittent 
            middleClasses = [mc for mc in type(self).__mro__[1:-2]]
            for mc in middleClasses:
                for key in mc.__annotations__.keys():
                    if type(self.__dataclass_fields__[name].metadata).__name__ == 'mappingproxy':
                        self.__dataclass_fields__[key].metadata = mc.__dataclass_fields__[key].metadata
        if 'options' in field.metadata:
            if isinstance(field.metadata['options'],Iterable):
                if self.__dict__[name] not in field.metadata['options']:
                    self.logWarning(f"{self.__dict__[name]} is not valid")
                    self.logError(msg=f'{name} must be one of {field.metadata["options"]}')
            else:
                if self.__dict__[name] != field.metadata['options']:
                    self.logError(msg=f'{name} must be {field.metadata["options"]}')

    def loadFromYaml(self):
        defaultOverwrites = [
            'dateModified'
        ]
        root,fn = os.path.split(self.yamlConfigFile)
        if os.path.exists(self.yamlConfigFile):
            self.logMessage(f'Loading: {self.yamlConfigFile}')
            tmp,self.header = loadDict(fileName=self.yamlConfigFile,returnHeader=True)
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
                    self.logChoice(f'User input {key}:{self.__dict__[key]} does not match the configuration in \n{self.yamlConfigFile}\n proceeding will overwrite ')
        elif os.path.isdir(root) and os.listdir(root) != []:
            self.logError(f'Root path {root} exists amd is not empty but is missing {fn}. Please check.')
    
    def saveToYaml(self,repr=True,inheritance=False):
        self.logWarning(type(self).__name__)
        if repr: keys = list(self.__annotations__.keys())
        else: keys = list(self.__dataclass_fields__.keys())
        if hasattr(self,'header'):
            header=self.header
        else:
            header=None
        saveDict(
            dcToDict(self,repr=True,inheritance=False),
            fileName=self.yamlConfigFile,
            header=header
        )

    def newField(self,name,value,kwargs={}):
        self.logWarning('Adding new dataclass dependency')
        self.__dataclass_fields__[name] = field(default_factory=value(**kwargs))
        self.__dataclass_fields__[name].name = name
        self.__dataclass_fields__[name].type = type(value)
        self.__annotations__[name] = type(value)
        self.__dict__[name] = self.__dataclass_fields__[name].default_factory
        
    def syncAttributes(self,incoming,inheritance=False,overwrite=False):
        excl = baseFunctions.__dataclass_fields__.keys()
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
        out = log(msg,traceback=traceback,verbose=verbose,cf=currentframe())
        self.updateLog(out)
        return(out)

    def updateLog(self,out):
        self.logFile=self.logFile+'\n\n'+out
