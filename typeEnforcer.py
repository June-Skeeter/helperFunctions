from dataclasses import dataclass, field

@dataclass
class typeEnforcer:
    verbose: bool = field(default=False,repr=False,metadata={'description': 'Enable verbose output for type coercion warnings'})

    def __post_init__(self):
        for (name, field_type) in self.__annotations__.items():
            if not isinstance(self.__dict__[name], field_type) and self.__dict__[name] is not None:
                current_type = type(self.__dict__[name])
                if self.verbose:
                    print(f"Type mismatch for field `{name}`: expected {field_type}, got {current_type}. Attempting to coerce.")
                if hasattr(field_type, '__module__') and field_type.__module__ == 'builtins':
                    try:
                        setattr(self, name,  field_type(self.__dict__[name]))
                    except:
                        raise TypeError(f"The field `{name}` was assigned by `{current_type}` instead of `{field_type}` and could not be coerced.")
                elif self.verbose:
                    print('Cannot coerce custom type')
            
