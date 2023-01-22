'''
    LCD Display Handler
    
    Will (eventually) display on a high resolution
    LCD using a single smaller buffer that breaks
    up the larger LCD into multiple "panels".

'''

from psos_svc import PsosService
import uasyncio
import queue
import time

from svc_msg import SvcMsg
import psos_util

from lcd_3inch5 import LCD
import color_brg_556 as clr

lcd_width = const(480)
lcd_height = const(320)

panel_width = const(160)
panel_height = const(80)

col_cnt = lcd_width/panel_width   # number of panel columns
row_cnt = lcd_height/panel_height # number of panel rows

char_width = const(8)
char_height = const(16)

panel_row_chr_cnt = panel_width/char_width
panel_col_chr_cnt = panel_height/char_height

c_bkgrnd = clr.BLACK
c_fgrnd  = clr.WHITE

    
    
# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)

        spi_svc = parms.get_parm("spi")
        self.spi_svc = self.get_svc(spi_svc)
        # spi = self.spi_svc.get_spi()

        self.lcd = LCD(self.spi_svc.spi,panel_width,panel_height)
                
        self.mqtt_log = [""]*20
        self.curr_pos = 0
        
        self.locked = False
                
    
    # Lock LCD so only one task writing to it at a time
    async def lock(self):
        i = 0
        while self.locked:
            await uasyncio.sleep_ms(100)
            i = i + 1
            if i > 45:
                raise Exception('waited too long for svc_dsp lock') 
        
        self.locked = True
        
        # Also lock the SPI
        # which will be needed to write to the display
        await self.spi_svc.lock()
        
    def unlock(self):
        self.spi_svc.unlock()
        self.locked = False


