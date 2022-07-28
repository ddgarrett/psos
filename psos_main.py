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
 
async def main(parms):
        
    # globally accessible default parameters
    defaults = parms["defaults"]
    
    # globally accessible service instances
    services = {}
    defaults["services"] = services
    
    print("main: create service objects")
    for svc_parms in parms["services"]:
        
        # create module specific parms object
        psos_parms = PsosParms(svc_parms,defaults)
        
        # create a new instance of a service
        # and store as a service under specified name
        name = svc_parms["name"]
        module_name = svc_parms["module"]
        
        print("... " + name)
        module = __import__(module_name)
        services[name] =  module.ModuleService(psos_parms)
        
        
    print("main: starting services")
    for svc_parms in parms["services"]:
        name = svc_parms["name"]
        svc  = services[name]
        
        # print("... " + name)
        uasyncio.create_task(svc.run())
        
    # gc.collect()
    
    while True:
        # nothing to do here, but can't return?
                    
        # allow co-routines to execute
        # print("main: free space "+str(gc.mem_free()))
        await uasyncio.sleep_ms(5000)
        

