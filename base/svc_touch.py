'''
    LCD Touch Handler
    
    Determines x,y co-ordinate of a touch on the LCD

'''

from psos_svc import PsosService
import uasyncio
import queue
import time

from svc_msg import SvcMsg
import psos_util

from lcd_touch import Touch

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
    
# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)

        spi_svc = parms.get_parm("spi")
        self.spi_svc = self.get_svc(spi_svc)
        
        self.regions = self.get_parm("regions")

        self.touch = Touch(self.spi_svc)
        
        # todo: make these a parm and customization value
        self.x_min = 385  # x = 0
        self.x_max = 3809 # x=480
        self.x_range = self.x_max - self.x_min
        
        self.y_min = 451  # y=320
        self.y_max = 3504 # y=0
        self.y_range = self.y_max - self.y_min

    async def run(self):
        
        mqtt = self.get_mqtt()
        
        while True:
            touch = await self.get_touch()
            if touch != None:
                for r in self.regions:
                    if self.in_region(r,touch[0],touch[1]):
                        await mqtt.publish(r["pub"],{"x":touch[0],"y":touch[1]})
                
            await uasyncio.sleep_ms(330)
                
    def in_region(self,rgn,x,y):
        
        outside = (
            x < rgn["x"] or
            y < rgn["y"] or
            x > (rgn["x"]+rgn["w"]) or
            y > (rgn["y"]+rgn["h"]) )
        
        return not outside

        
    # Return the x,y coordinates of a touch.
    # If no touch, return None
    async def get_touch(self):
        
        # may have to wait for a lock on the SPI
        get = await self.touch.get_touch()
        
        # print(get)
        if get != None and get[0] != 0 and get[1] != 0:
            # await self.spi_svc.lock() # self.lcd_locked = True
            
            # self.lcd.write_cmd(0x20) # invert
            x = get[0]
            x = min(self.x_max,x)
            x = max(self.x_min,x)
            x_pt = round((x-self.x_min)/self.x_range*480)
            
            y = get[1]
            y = min(self.y_max,y)
            y = max(self.y_min,y)
            y_pt = round((1-(y-self.y_min)/self.y_range)*320)
            
            return(x_pt,y_pt)
            
        return None

