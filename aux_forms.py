from itertools import chain
import re 

#This is a list of common helper functions used throughout this bot.
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

def concatenator(itemlist):
    counter = 1
    titlelist = []
    for item in itemlist:
        newline = f'{counter}. {item.title}'
        titlelist.append(newline)
        counter += 1
    string = '\n'
    return(string.join(titlelist))
