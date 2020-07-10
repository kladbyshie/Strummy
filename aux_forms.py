from itertools import chain
import re 

def argsmachine(*args):
    newargs = []
    args = [x for x in chain.from_iterable(args)]
    for item in args:
        item = re.sub(' +', '',item)
        newargs.append(item)
    query = ' '.join(newargs)
    return(query)

def read_token(num):
    with open("token.txt", "r") as tok:
        lines = tok.readlines()
        return(lines[num].strip())
