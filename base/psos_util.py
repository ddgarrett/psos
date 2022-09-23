'''
    Utility functions
'''

import ujson

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
    