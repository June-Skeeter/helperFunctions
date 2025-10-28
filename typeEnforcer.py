from dataclasses import dataclass, field
from .log import log

@dataclass
class typeEnforcer:
    verbose: bool = field(default=False,repr=False,metadata={'description': 'Enable verbose output for type coercion warnings'})
    
    def __post_init__(self):
        for (name, field) in self.__dataclass_fields__.items():
            field_type = field.type
            if not isinstance(self.__dict__[name], field_type) and self.__dict__[name] is not None:
                current_type = type(self.__dict__[name])
                if self.verbose:
                    self.error(f"Type mismatch for field `{name}`: expected {field_type}, got {current_type}. Attempting to coerce.",kill=False)
                if hasattr(field_type, '__module__') and field_type.__module__ == 'builtins':
                    try:
                        setattr(self, name,  field_type(self.__dict__[name]))
                    except:
                        raise TypeError(f"The field `{name}` was assigned by `{current_type}` instead of `{field_type}` and could not be coerced.")
                elif self.verbose:
                    self.error('Cannot coerce custom type')
            if 'options' in field.metadata:
                if self.__dict__[name] not in field.metadata['options']:
                    self.error(msg=f'{name} must be one of {field.metadata["options"]}')

    def error(self,msg='',ln=False,fn=False,kill=True):
        print(msg)
        log(msg=msg,ln=False,fn=False,kill=True,verbose=True)
            
