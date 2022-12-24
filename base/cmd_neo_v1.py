"""
    Command to Test Neopixel.
    
    Display a single color who's brightness and hue
    can be changed via the gyro.
    
"""

from psos_svc import PsosService
import uasyncio
import sys

import machine
import neopixel
import hsv_to_rgb

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self.menu = self.get_parm("menu")
        
        gyro  = self.get_parm("gyro","gyro")
        self.gyro = self.get_svc(gyro)
        
        # rp2 bug workaround
        if self.is_rp2():
            import rp2
            rp2.PIO(0).remove_program()
            
        # use neopixel instead of WS2812 to work on ESP32
        # as well as rp pico
        pin = self.get_parm("pin",0)
        self.ws = neopixel.NeoPixel(machine.Pin(pin),8)
        
    async def run(self):
        self.gyro.lock_gyro(True)
        
        self.o = self.svc_lcd.lcd
                
        h = 0.0  # hue
        s = 1.0  # saturation
        v = 0.0  # value (brightness)
        
        self.menu.update_lcd("h: 0.00\ns: 1.00\nv: 0.00")
        last_hsv = await self.show_hsv((h,s,v),[-1,-1,-1])
        
        r = "--"

        while True:
            r,msg = await self.gyro.poll_chg(st=r)
            
            if msg == "over":
                self.gyro.lock_gyro(False)
                self.neo_rgb(0,0,0)
                return
            
            if msg == "right":
                h += .02
                if h > 1.0:
                    h = 0
            elif msg == "left":
                h -= .02
                if h < 0:
                    h = 1.0
            elif msg == "up":
                v += .02
                v = min(v,.5)
            elif msg == "down":
                v -= .02
                v = max(v,0)
                
            last_hsv = await self.show_hsv((h,s,v),last_hsv)
            self.neo_hsv(h,s,v)
            
    # show h,s,v on neopixel
    def neo_hsv(self,h,s,v):
        r,g,b = hsv_to_rgb.cnv(h,s,v)
        self.neo_rgb(r,g,b)
        
    # show r,g,b on neopixel
    def neo_rgb(self,r,g,b):
        for j in range(8):
            self.ws[j] = [r,g,b]
        self.ws.write()
        
    # show changed h,s,v values on OLED
    async def show_hsv(self,hsv,last_hsv):
        col = 3 # column to display in

        for row in range(3):
            if last_hsv[row] != hsv[row]:                    
                self.o.move_to(col,row)
                self.o.putstr("{:0.2f}".format(hsv[row]))
                last_hsv[row] = hsv[row]
                
        return last_hsv
