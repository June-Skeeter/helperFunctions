# replace all non-alphanumeric characters with a safe value
import re
import string
printable = set(string.printable)

# Formats string to be printable
def cleanString(stringIn):
    stringOut = ''.join(filter(lambda x: x in printable, stringIn))
    return(stringOut)


# Formats string to be safe for a filename (replaces all non alphanumeric characters with underscores by default)
def safeFormat(stringIn,safeCharacters='[^0-9a-zA-Z-]+',safeFill='_'):
    stringOut = re.sub(safeCharacters,safeFill, str(stringIn)).rstrip(safeFill).lstrip(safeFill)
    if stringOut == '':
        stringOut = safeFill
    return(stringOut)