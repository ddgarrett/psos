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
import os
import uasyncio
from machine import ADC, Pin
import queue

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self.q = queue.Queue()
        self.sub = parms.get_parm("sub")
        self.pub = parms.get_parm("pub")
        
        self.adc = ADC(Pin(self.get_parm("pin")))
        
        if self.is_esp32():
            # configure the ESP32 adc
            self.adc.atten(ADC.ATTN_11DB)

        # self.wet = self.get_parm("wet",25000)
        # self.dry = self.get_parm("dry",58000)
        self.cycles = self.get_parm("cycles",5)
        
        self.cust = self.read_cust()
        if self.cust == None:
            self.cust = {
                "wet":self.get_parm("wet",25000),
                "dry":self.get_parm("dry",58000)}
        
    async def run(self):
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self.sub,self.q)
        
        while True:
            data = await self.q.get()
            r = await self.get_adc_value()
            await mqtt.publish(self.pub,r)

    async def get_adc_value(self):
        dry = self.cust["dry"]
        wet = self.cust["wet"]
        
        cycle=5
        raw = 0

        for _ in range(cycle):
            r = self.adc.read_u16()
            raw += r
            await uasyncio.sleep_ms(100)
            
        raw /= cycle
        raw = round(raw)

        raw_c = min(dry,raw)
        raw_c = max(wet,raw_c)

        sm = int(round(((raw_c - dry) / (wet - dry)) * 100))
        sm1 = int(round(((raw_c - dry) / (wet - dry)) * 10))
        
        return {"lvl_100":sm, "lvl_10":sm1, "raw":raw, "dev":self.dev}
