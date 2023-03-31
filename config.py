"""
    Load Configuration File and Configure sys.path
    
    
    To set path config and access config.json values:
    
        import config
        cfg = config.cfg
    
    The above code loads the config.json file into the
    a dictionary named cfg
    
"""

import ujson
import sys

# load a json file
# here because we can't use the psos_util
# until after loading config.json
def load_json(fn):
    # read the paramter file
    with open(fn) as f:
        parms = ujson.load(f)
        f.close()
        return parms
    
    return None

# read main configuration file
cfg = load_json("config.json")
print("boot: config",cfg)

# extend module search path
if "path" in cfg:
    sys.path.extend(cfg["path"]) 
