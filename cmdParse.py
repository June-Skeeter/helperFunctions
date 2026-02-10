import json
import argparse


def str2bool(v):
    # credit: https://stackoverflow.com/a/43357954/5683778
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
    
def cmdParse(defaultArgs,debug=False):
    # helper function to parse command line arguments
    CLI=argparse.ArgumentParser()
    dictArgs = []
    for key,val in defaultArgs.items():
        dt = type(val)
        nargs = "?"
        if debug:
            print(key,val,dt)
        if val == None:
            dt = str
        if dt == type({}):
            dictArgs.append(key)
            dt = type('')
            val = '{}'
        elif dt == type([]):
            nargs = '+'
            dt = type('')
        elif dt == type(False):
            dt = str2bool
        CLI.add_argument(f"--{key}",nargs=nargs,type=dt,default=val)

    # parse the command line
    args = CLI.parse_args()
    kwargs = vars(args)
    for d in dictArgs:
        kwargs[d] = json.loads(kwargs[d])
        # replace booleans
    if debug:
        print(kwargs)
    return(kwargs)