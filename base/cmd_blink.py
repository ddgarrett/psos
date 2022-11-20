"""
    Command to Blink Internal LED Service
        
    Blink internal LED specified times then exit.
    Command version of svc_blink.
    
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
        pin = self.get_parm("pin",2)
        self._led = Pin(pin, Pin.OUT)

        self.cnt = self.get_parm("cnt",30)
        
    async def run(self):
        
        i = self.cnt
        
        while True:
            await uasyncio.sleep_ms(500)
            self._led(1)
            await uasyncio.sleep_ms(500)
            self._led(0)
            
            i -= 1
            if i <= 0:
                return
