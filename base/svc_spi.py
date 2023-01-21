"""
    SPI Service Class
    
    Set up an SPI Connection which other services can use.
    
"""

from psos_svc import PsosService
from machine import Pin,SPI,PWM
import gc

class ModuleService(PsosService):

    def __init__(self,parms):
        super().__init__(parms)

        # below are defaults for WaveShare 13.5" LCD
        slot = self.get_parm("slot",1)
        sck  = self.get_parm("sck",10)
        mosi = self.get_parm("mosi",11)
        miso = self.get_parm("miso",12)
        baud = self.get_parm("baud",5_000_000)
        
        # self.spi = SPI(slot,baud,sck=Pin(sck),mosi=Pin(mosi),miso=Pin(miso))
        
        self.default = {"slot":slot, "sck":sck, "mosi":mosi, "miso":miso, "baud":baud}
        self.locked = False
        self.reset()
        
    # reset to the default SPI configuration
    # also sets locked to False
    def reset(self):
        p = self.default
        self.spi = SPI(p["slot"],p["baud"],sck=Pin(p["sck"]),mosi=Pin(p["mosi"]),miso=Pin(p["miso"]))
        self.unlock()
        
    def unlock(self):
        self.locked = False
        
    async def lock(self):
        i = 0
        while self.locked:
            await uasyncio.sleep_ms(330)
            i = i + 1
            if i > 45:
                raise Exception('waited too long for spi lock') 
            
        self.locked = True
        
    def get_spi(self):
        return self.spi
    
    def set_spi(self,baud,sck,mosi,miso):
        await self.lock()
        slot = self.default["slot"]
        gc.collect()
        self.spi = SPI(slot,baud,sck=Pin(sck),mosi=Pin(mosi),miso=Pin(miso))
        return self.spi
        
    
        
        
            

