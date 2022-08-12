"""
    Reset an ESP8266
    
    Two ways to use this service:
    
    1. send a message to the subscr_upd topic specifiec in the JSON file
    
    2. programmatically, another service can get the reset service and call the reset method
          svc = self.get_svc("reset")
          await svc.reset()
       
    For more reliable reset this service pushes a pin connected to the reset high.
    Default is pin 5 (D1)
    
"""

from psos_svc import PsosService
import uasyncio
import queue

from machine import Pin

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        # when a message is received via the subscribed topic
        # data is written to the trigger_q
        self._subscr_topic = parms.get_parm("subscr_upd")
        self._trigger_q = queue.Queue()
        
        pin = self.get_parm("pin",5)
        self._rst = Pin(pin,mode=Pin.OUT,value=1)

        
    async def run(self):
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self._subscr_topic,self._trigger_q)
        
        while True:
            data = await self._trigger_q.get()
            await self.reset(data[2])
            
            
    # reset system by pushing pin connect to reset high (0)
    async def reset(self,data=None):
        print("resetting system, reason: ",data)
        await uasyncio.sleep_ms(1000) # give print time to run before resetting
        
        self._rst(0)

