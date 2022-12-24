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
        self.ws = neopixel.NeoPixel(machine.Pin(0),8)
        
        # task that rolls neopixel colors
        self.t = None
        
    async def run(self):
        self.gyro.lock_gyro(True)
        
        self.o = self.svc_lcd.lcd
                
        h = 0.0  # hue
        s = 1.0  # saturation
        v = 0.0  # value (brightness)
        
        self.menu.update_lcd("h: 0.00\ns: 1.00\nv: 0.00")
        last_hsv = await self.show_hsv((h,s,v),[-1,-1,-1])
        
        r = "--"
        cmd = "--"
        chg = False

        while True:
            r,msg = await self.gyro.poll_chg(st=r,ret_flat=True)
            
            if msg == "over":
                self.gyro.lock_gyro(False)
                self.neo_rgb(0,0,0)
                return
            
            chg = True
            if msg in ("right","left","--"):
                if cmd == msg:
                    chg = False
                else:
                    cmd = msg
            elif msg == "up":
                v += .02
                v = min(v,.5)
            elif msg == "down":
                v -= .02
                v = max(v,0)
                
            if chg:
                # print(r)
                last_hsv = await self.show_hsv((h,s,v),last_hsv)
                await self.start_roll(h,s,v,cmd)
                chg = False
            
    async def start_roll(self,h,s,v,cmd):
        if self.t != None:
            # print("canceling task")
            self.t.cancel()
            
        self.t = uasyncio.create_task(self.roll_neo(h,s,v,cmd))
        
        
    # task to show rolling h,s,v on neopixel
    # cmd = "left", "right" or "--"
    # if "--" don't roll
    async def roll_neo(self,h,s,v,cmd):
        
        h_incr = .125
            
        for i in range(8):
            h += h_incr
            if h > 1:
                h -= 1
                
            wy = hsv_to_rgb.cnv(h,s,v)
            self.ws[i] = [wy[0],wy[1],wy[2]]
                    
        if cmd == "--":
            self.ws.write()
            self.t = None
            return
        
        while True:
            if cmd == "left":
                s = self.ws[7]
                for j in range(7):
                    self.ws[7-j] = self.ws[7-j-1]
                    
                self.ws[0] = s
            else:
                s = self.ws[0]
                for j in range(6,-1,-1):
                    self.ws[6-j] = self.ws[6-j+1]
                
                self.ws[7] = s
                
            self.ws.write()
            await uasyncio.sleep_ms(100)
            
    # show a single r,g,b color on neopixel
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

