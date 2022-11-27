"""
    1. create new instance of each service modules
    2. start each of the services,
    3. enter loop but currently do nothing
        
    Services are defined in the "psos_parms.json"
    
    First two services must be wifi and mqtt.
    
    Mqtt service uses wifi to connect to an MQTT broker.
    
    Other services call mqtt to subscribe to topics
    and publish to topics.
    
    Mqtt polls for new messages to subscribed topics
    and forwards any messages via a queue associated with
    each subscription.
    
"""

import uasyncio
import gc
from psos_parms import PsosParms

# additional imports to load them now instead of later
import machine
# import network
import os
import psos_util
import secrets


async def main(parms,config):
        
    # globally accessible default parameters
    defaults = {}
    if "defaults" in parms:
        defaults = parms["defaults"]
    
    # globally accessible service instances
    services = {}
    defaults["services"] = services
    defaults["config"]   = config
    defaults["started"]  = False
    
    u = os.uname()
    defaults["sysname"]  = u.sysname
    defaults["has_wifi"] = True
    if u.sysname == "rp2":
        if not "Pico W" in u.machine:
            defaults["has_wifi"] = False    
    
    print("main: create service objects")
    gc.collect()
    
    for svc_parms in parms["services"]:
        
        # create module specific parms object
        psos_parms = PsosParms(svc_parms,defaults,config)
        
        # create a new instance of a service
        # and store as a service under specified name
        name = svc_parms["name"]
        module_name = svc_parms["module"]
        
        print("... " + name)
        module = __import__(module_name)
        services[name] =  module.ModuleService(psos_parms)
        
        gc.collect()
        
        
    print("main: starting services")
    for svc_parms in parms["services"]:
        name = svc_parms["name"]
        svc  = services[name]
        
        uasyncio.create_task(svc.run())
        gc.collect()
        
    # pmap = False
    defaults["started"] = True
    
    while True:
        # nothing to do here, but can't return?
                    
        # allow co-routines to execute
        # print("main: free space "+str(gc.mem_free()))
        gc.collect()
        await uasyncio.sleep_ms(5000)
        
        '''
        if not pmap:
            gc.collect()
            print("memory: ",gc.mem_free())
            pmap = True
            micropython.mem_info(1)
        '''