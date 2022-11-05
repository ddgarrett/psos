"""
    Capacitive Soil Sensor Service Class
    
    Send a number 0 through 10, to indicate degree of
    moisture in the soil.
    
    When a message for the topic specified by
    "sub" is received, send a JSON string to the
    topic specified by "pub". Format of JSON
    string is {"lvl":n} where "n" is a number
    from 0 to 10. 0 is dry. 10 is wet.
    
    Parms include an ADC value for dry (default 2700)
    and wet (default 1260).
    
"""

from psos_svc import PsosService
import uasyncio
from machine import ADC, Pin
import queue

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        pin = parms.get_parm("pin",32)
        print("pin:",pin)

        self.adc = ADC(Pin(pin))
        attenuation = ADC.ATTN_11DB
        self.adc.atten(attenuation)

        self.sub = parms.get_parm("sub") # subscribe topic
        self.q   = queue.Queue()         # q for subscribed messages
        self.pub = parms.get_parm("pub") # publish topic
        
        self.dry = parms.get_parm("dry",2525)
        self.wet = parms.get_parm("wet",1422)
        
        print("dry, wet: ",self.dry,self.wet)
        
    async def run(self):
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self.sub,self.q)
        
        while True:
            data = await self.q.get()
            await self.send_data(mqtt)
            
            
    # send data via MQTT
    async def send_data(self,mqtt):
        
        # sample 5 times and average,
        cnt = 5
        mv = 0
        while cnt > 0:
            mv += (self.adc.read_uv() / 1000)
            cnt = cnt - 1
            await uasyncio.sleep_ms(100)
            
        mv = mv/5
        
        # constrain value
        mv = min(self.dry,mv)
        mv = max(self.wet,mv)
        
        # map value to 0 to 10 range and publish
        mv = int(round(((mv - self.dry) / (self.wet - self.dry)) * 10))
        await mqtt.publish(self.pub,{"mv": mv})
            