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

# perform a one time formatting of
# fields in the defaults
# using the config dictionary
def format_defaults(defaults,config):
    try:
        no_fmt = defaults["no_fmt"]
    except KeyError:
        no_fmt = ["format"]
        
    for k,v in defaults.items():
        v = defaults
        if type(v) == str and '{' in v and not v in no_fmt:
            defaults[k] = v.format(**config)
        
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

# load a json
# based on config directory
def load_parms(config,fn):
    pfn = filepath(config["parms"],fn)
    return load_json(pfn)

# load a json file
def load_json(fn):
    # read the paramter file
    with open(fn) as f:
        parms = ujson.load(f)
        f.close()
        return parms
    
    return None

    
