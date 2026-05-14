import string
import random
def randomID(length=6,alphanumeric=True):
    if alphanumeric:
        characters = string.ascii_letters + string.digits
    else:
        characters = string.digits
    return(''.join(random.choices(characters,k=length)))