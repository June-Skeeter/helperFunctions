# print statements + more for debugging and logging outputs
from inspect import currentframe
import sys
def log(msg='',ln=True,fn=True,verbose=True,kill=False):
    if verbose:
        if type(msg) == list or type(msg) == tuple:
            msg = ' '.join([str(m) for m in msg])
        if ln:
            cf = currentframe()
            msg = f"line {cf.f_back.f_lineno}:\n{msg}"
            if fn:
                cf.f_back.f_code.co_filename
                msg = f"{cf.f_back.f_code.co_filename} "+ msg
        if kill:
            sys.exit('\nError:\n'+msg)
        else:
            print(msg)
    else:
        return(msg)
