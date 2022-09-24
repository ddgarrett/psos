"""
    Boot up PSOS (Publish/Subscribe OS)
    
    Read parameter file to start up clients.
"""

import ujson
import uasyncio
import gc

# print("0_boot: start - free space "+str(gc.mem_free()))

# read the paramter file
with open("psos_parms.json") as f:
        parms = ujson.load(f)

# start main
if "name" in parms:
    print("boot: starting",parms["name"])
          
main_name = parms["main"]
print("boot: starting " + main_name)

main = __import__(main_name)
uasyncio.run(main.main(parms))
