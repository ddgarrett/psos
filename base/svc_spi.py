"""
    SPI Service Class
    
    Set up an SPI Connection which other services can use.
    
"""

from psos_svc import PsosService
from machine import Pin,SPI,PWM
import gc
import uasyncio 

class ModuleService(PsosService):

    def __init__(self,parms):
        super().__init__(parms)

        # below are defaults for WaveShare 13.5" LCD
        slot = self.get_parm("slot",1)
        sck  = self.get_parm("sck",10)
        mosi = self.get_parm("mosi",11)
        miso = self.get_parm("miso",12)
        baud = self.get_parm("baud",5_000_000)
        
        self.baud = baud
        
        # self.spi = SPI(slot,baud,sck=Pin(sck),mosi=Pin(mosi),miso=Pin(miso))
        
        self.default = {"slot":slot, "sck":sck, "mosi":mosi, "miso":miso, "baud":baud}
        self.locked = False
        self.reset()
        
    # reset to the default SPI configuration
    def reset(self):
        p = self.default
        self.spi = SPI(p["slot"],baudrate=p["baud"],sck=Pin(p["sck"]),mosi=Pin(p["mosi"]),miso=Pin(p["miso"]))
        # print("reset:",self.spi)
        
    def exit_svc(self):
        try:
            self.spi.deinit()
            print("spi deinit")
        except:
            pass
        
    # change baud rate to specified value.
    # IF no value specified, set it to the original value
    def reinit(self,baud=None):
        if baud == None:
            baud = self.baud

        self.spi.init(baudrate=baud)
        # print("reinit:",self.spi)
        
    def unlock(self,baud=None):
        self.reinit(baud=baud)
        # print("unlock:",self.spi)
        self.locked = False
        
    async def lock(self,baud=None):
        i = 0
        while self.locked:
            await uasyncio.sleep_ms(100)
            i = i + 1
            if i > 45:
                raise Exception('waited too long for spi lock') 
            
        self.locked = True
        self.reinit(baud)
        # print("lock:",self.spi)
        
    def get_spi(self):
        return self.spi
    
    def set_spi(self,baud,sck,mosi,miso):
        await self.lock()
        slot = self.default["slot"]
        gc.collect()
        self.spi = SPI(slot,baud,sck=Pin(sck),mosi=Pin(mosi),miso=Pin(miso))
        return self.spi
        
    
        
        
            

