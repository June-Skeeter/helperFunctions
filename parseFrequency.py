import re
#Parse a measurement frequency from assorted string input formats to a standard format compatible with pandas datetime

def parseFrequency(text):
    def split_digit(s):
        match = re.search(r"\d", s)
        if match:
            s = s[match.start():]
        return s 
    freqDict = {'MSEC':'ms','Usec':'us','Sec':'s','HR':'h','MIN':'min'}
    freq = split_digit(text)
    for key,value in freqDict.items():
        freq = re.sub(key.lower(), value, freq, flags=re.IGNORECASE)
    freq = re.sub(r'[^a-zA-Z0-9]','',freq)
    return(freq)