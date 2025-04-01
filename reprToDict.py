# given a dataclass, dump items where repr=true to a dictionary
def reprToDict(dc):
    return({k:v for k,v in dc.__dict__.items() if k in dc.__dataclass_fields__ and dc.__dataclass_fields__[k].repr})