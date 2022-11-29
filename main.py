"""
    Boot up PSOS (Publish/Subscribe OS)
    
    Read parameter file to start up clients.
"""

import ujson
import uasyncio
import gc
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
config = load_json("config.json")
print("boot: config",config)

# extend module search path
if "path" in config:
    sys.path.extend(config["path"]) 

# now that we have path configured
# we can import psos_util
import psos_util

# read parms for a given device
# from root directory if it's there
# otherwise read from config specified parms directory
pfn = config["device"]+"_psos_parms.json"
parms = psos_util.load_parms(config,pfn)

# start main
if "name" in parms:
    print("boot:",parms["name"])
          
main_name = parms["main"]
print("boot: starting " + main_name)

main = __import__(main_name)
uasyncio.run(main.main(parms,config))