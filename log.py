# print statements + more for debugging and logging outputs
from inspect import currentframe
import sys
def log(msg='',ln=True,fn=True,verbose=True,kill=False):
    if verbose:
        if type(msg) == list or type(msg) == tuple:
            msg = ' '.join([str(m) for m in msg])
        if ln or fn:
            cf = currentframe()
            if fn:
                msg = f"{msg}\{cf.f_back.f_code.co_filename}"
            if ln:
                msg = f"{msg}\nLine #:{cf.f_back.f_lineno}"
        if kill:
            sys.exit('\nError:\n'+msg)
        else:
            print(msg)
    else:
        return(msg)
