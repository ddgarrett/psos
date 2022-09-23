"""
    Blink Internal LED Service
        
    Blink internal LED on either D1 Mini or ESP32.
    
"""

from psos_svc import PsosService
import uasyncio

from machine import Pin

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        # Service specific initialization
        # Set LED pin out
        self._led = Pin(2, Pin.OUT)
        print("in svc_blink.__init__")
        
    async def run(self):
        
        print("in svc_blink.run")
        
        while True:
            await uasyncio.sleep_ms(500)
            self._led(1)
            await uasyncio.sleep_ms(500)
            self._led(0)
            
            
