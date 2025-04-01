# replace all non-alphanumeric characters with a safe value
import re
def safeFormat(string,safeCharacters='[^0-9a-zA-Z]+',safeFill='_'):
    return(re.sub(safeCharacters,safeFill, str(string)))