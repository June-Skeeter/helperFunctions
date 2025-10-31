from dataclasses import dataclass, field
from .parseCoordinates import parseCoordinates
from .dictFuncs import dcToDict,loadDict,saveDict
from .log import log
import os

# Useful collection of parentclass functions
@dataclass
class baseFunctions:
    verbose: bool = field(default=True,repr=False) # Enable verbose output for type coercion warnings
    yamlConfigFile: str = field(default=None,repr=False) # If valid yaml file path is provided, the dataclass will read from the file
    typeCheck: bool = field(default=True,repr=False)
    message: str = field(default='',repr=False)
    
    def __post_init__(self):
        if self.yamlConfigFile:
            self.loadFromYaml()
        if not self.typeCheck:
            return
        for (name, field) in self.__dataclass_fields__.items():
            field_type = field.type
            if not isinstance(self.__dict__[name], field_type) and self.__dict__[name] is not None:
                current_type = type(self.__dict__[name])
                if self.verbose:
                    self.logWarning(f"\nType mismatch for field: `{name}`\nExpected input of {field_type.__name__}, received input of {current_type.__name__}\nAttempting to coerce value: {self.__dict__[name]}",hold=True)
                if hasattr(field_type, '__module__') and field_type.__module__ == 'builtins':
                    try:
                        if name in parseCoordinates.__annotations__.keys():
                            pC = parseCoordinates(**{name:self.__dict__[name]})
                            self.__dict__[name] = pC.__dict__[name]
                            self.logWarning(f'Confirm coordinate parsed correctly: {self.__dict__[name]}')
                        else:
                            setattr(self, name,  field_type(self.__dict__[name]))
                            self.logWarning(f'Confirm variable coerced correctly: {self.__dict__[name]}')
                    except:
                        self.logError(f"The field `{name}` was assigned by `{current_type.__name__}` instead of `{field_type.__name__}` and could not be coerced to required type.")
                elif self.verbose:
                    self.logError('Cannot coerce custom type')
            if 'options' in field.metadata:
                if self.__dict__[name] not in field.metadata['options']:
                    self.logError(msg=f'{name} must be one of {field.metadata["options"]}')

    def loadFromYaml(self):
        defaultOverwrites = [
            'dateModified'
        ]
        root,fn = os.path.split(self.yamlConfigFile)
        if os.path.exists(self.yamlConfigFile):
            self.logAction(f'Loading: {self.yamlConfigFile}')
            tmp,self.header = loadDict(fileName=self.yamlConfigFile)
            for key,value in tmp.items():
                if self.__dict__[key] is None:
                    setattr(self,key,value)
                elif self.__dict__[key] != value and key not in defaultOverwrites:
                    self.logChoice(f'User input {key}:{self.__dict__[key]} does not match the configuration in \n{self.yamlConfigFile}\n proceeding will overwrite ')
        elif os.path.isdir(root) and os.listdir(root) != []:
            self.logError(f'Root path {root} exists amd is not empty but is missing {fn}. Please check.')
    
    def saveToYaml(self,repr=True,inheritance=False):
        print(type(self).__name__)
        if hasattr(self,'header'):
            header=self.header
        else:
            header=None
        # print('\n\n',self.yamlConfigFile,'\n\n')
        saveDict(
            dcToDict(self,repr=True,inheritance=False),
            fileName=self.yamlConfigFile,
            header=header
        )
        
    def snycAttributes(self,incoming,inheritance=False,overwrite=False):
        # Add attributes of one class to another and avoid ciruclar imports
        if inheritance:
            keys = list(incoming.__dataclass_fields__.keys())
        else:
            keys = list(incoming.__annotations__.keys())
        for key in keys:
            if not hasattr(self,key):
                setattr(self,key,incoming.__dict__[key])
            elif overwrite and self.__dict__[key] != incoming.__dict__[key]:
                setattr(self,key,incoming.__dict__[key])
                

    def logError(self,msg='',kill=True):
        log(msg=f'\n\n{"*"*10} Error {"*"*10}\n{msg}\n',ln=False,fn=False,kill=kill,verbose=True)

    def logWarning(self,msg='',hold=False,ln=False,fn=False):
        if hold == True:
            self.message = '\n'.join([self.message, msg])
        else:
            self.message = '\n'.join([self.message, msg])
            log(msg=f'\n\n{"*"*10} Warning {"*"*10}\n{self.message}\n',ln=ln,fn=fn,verbose=True)
            self.message = ''

    def logChoice(self,msg,proceed='Y'):
        log(msg=msg,)
        i = input(f'Enter {proceed} to continue or any other key to exit: ')
        if i == proceed:
            return
        else:
            log(msg='Exiting',kill=True)

    def logAction(self,msg):
        log(msg,fn=False,ln=False)
            

    # def logMessage(self,msg):
