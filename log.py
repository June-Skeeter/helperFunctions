# output statements to console + more for debugging and logging outputs
# Need to add option for capturing console outputs?
from inspect import currentframe
import sys
def log(msg='',ln=True,fn=True,verbose=True,kill=False,cf=None):
    if verbose:
        if type(msg) == list or type(msg) == tuple:
            msg = ' '.join([str(m) for m in msg])
        if ln or fn:
            if cf is None:
                cf = currentframe()
            if fn or ln:
                msg = f'{msg}\n"{cf.f_back.f_code.co_filename}", line {cf.f_back.f_lineno}\n'
        if kill:
            sys.exit(msg+'\nExiting Program')
        else:
            print(msg)
    else:
        return(msg)
