'''
    Utility functions
'''

import ujson
import os
import sys

def to_str(t):
    if type(t) == str:
        return t
    
    if type(t) == bytes:
        return t.decode("utf-8")
    
    return str(t)

def to_bytes(t):
    if type(t) == bytes:
        return t
    
    if type(t) == str:
        return t.encode("utf-8")
    
    return ujson.dumps(t).encode("utf-8")
    
# return the file path of a file,
# checking the base directory first
# then the passed directory name
def filepath(dir,fn):
    # first root directory
    if fn in os.listdir():
        return fn
    
    if fn in os.listdir(dir):
        return dir+"/"+fn
    
    return None

    