"""
    General Reset Service
    
    Two ways to use this service:
    
    1. send a message to the sub topic specifiec in the JSON file
    
    2. programmatically, another service can get the reset service and call the reset method
          svc = self.get_svc("reset")
          svc.reset()
       
    NOTE: that if this service is not named "reset" it will not be called by the
    psos_svc reset method, which works fine as well.
    
"""

from psos_svc import PsosService
import uasyncio
import queue

import machine
import time

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
    async def run(self):
        
        mqtt = self.get_mqtt()
        q = queue.Queue()
        await mqtt.subscribe(self.get_parm("sub"),q)
        
        while True:
            data = await q.get()
            # super().reset will call this reset
            # after logging reset reason
            await super().reset(data[2])
            
            
    # reset system by pushing pin connect to reset high (0)
    def reset(self,rsn=None):
        print("resetting system, reason: ",rsn)
        time.sleep_ms(1000) # give print time to run before resetting
        machine.reset()
        time.sleep_ms(5000) # in case reset is not immediate
