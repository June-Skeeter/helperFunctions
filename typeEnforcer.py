from dataclasses import dataclass, field
from .parseCoordinates import parseCoordinates
from .log import log

@dataclass
class typeEnforcer:
    verbose: bool = field(default=True,repr=False,metadata={'description': 'Enable verbose output for type coercion warnings'})
    message: str = ''
    
    def __post_init__(self):
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
                    except:
                        self.logError(f"The field `{name}` was assigned by `{current_type.__name__}` instead of `{field_type.__name__}` and could not be coerced to required type.")
                elif self.verbose:
                    self.logError('Cannot coerce custom type')
            if 'options' in field.metadata:
                if self.__dict__[name] not in field.metadata['options']:
                    self.logError(msg=f'{name} must be one of {field.metadata["options"]}')

    def logError(self,msg='',kill=True):
        log(msg=f'\n\n{"*"*10} Warning {"*"*10}\n{msg}\n'+msg,ln=False,fn=False,kill=kill,verbose=True)

    def logWarning(self,msg='',hold=False,ln=False,fn=False):
        if hold == True:
            self.message = '\n'.join([self.message, msg])
        else:
            self.message = '\n'.join([self.message, msg])
            log(msg=f'\n\n{"*"*10} Warning {"*"*10}\n{self.message}\n',ln=ln,fn=fn,verbose=True)
            self.message = ''
            

    # def logMessage(self,msg):
