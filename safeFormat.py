# replace all non-alphanumeric characters with a safe value
import re
import string
printable = set(string.printable)

# Formats string to be printable
def cleanString(stringIn,replace={},permit=set()):
    if isinstance(permit,str):
        permit=set(permit)
    elif isinstance(permit,list):
        permit=set(permit)
    permit.update(printable)
    for k,v in replace.items():
        stringIn = stringIn.replace(k,v)
    stringOut = ''.join(filter(lambda x: x in permit, stringIn))
    return(stringOut)


# Formats string to be safe for a filename (replaces all non alphanumeric characters with underscores by default)
def safeFormat(stringIn,safeCharacters='[^0-9a-zA-Z-]+',safeFill='_'):
    stringOut = re.sub(safeCharacters,safeFill, str(stringIn)).rstrip(safeFill).lstrip(safeFill)
    if stringOut == '':
        stringOut = safeFill
    return(stringOut)