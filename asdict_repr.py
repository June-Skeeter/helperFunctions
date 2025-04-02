# given a dataclass, dump items where repr=true to a dictionary
def asdict_repr(dc,repr=True):
    if repr:
        return({k:v for k,v in dc.__dict__.items() if k in dc.__dataclass_fields__ and dc.__dataclass_fields__[k].repr})
    elif repr is None:
        return({k:v for k,v in dc.__dict__.items() if k in dc.__dataclass_fields__})
    else:
        return({k:v for k,v in dc.__dict__.items() if k in dc.__dataclass_fields__ and not dc.__dataclass_fields__[k].repr})