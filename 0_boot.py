"""
    Boot up PSOS (Publish/Subscribe OS)
    
    Read parameter file to start up clients.
"""

import ujson
import uasyncio

# read the paramter file
with open("psos_parms.json") as f:
        parms = ujson.load(f)

# start main
if "name" in parms:
    print("starting",parms["name"])
          
main_name = parms["main"]
print("starting " + main_name)

main = __import__(main_name)
uasyncio.run(main.main(parms))
    



