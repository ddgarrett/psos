"""
    Command to Customize Soil Dry and Wet Readings.
    
"""

from psos_svc import PsosService
import uasyncio
import sys
import gfx

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self.menu = self.get_parm("menu")
        
        svc_gyro  = self.get_parm("svc_gyro")
        self.gyro = self.get_svc(svc_gyro)
        
    async def run(self):
        self.gyro.lock_gyro(True)
        self.svc_lcd.clear_screen()

        self.o = self.svc_lcd.lcd
        self.g = self.svc_lcd.lcd.gfx # graphics
        
        # initialize values and display
        c = await self.gyro.poll_gyro()
        self.last_c = [1000,1000,1000]
        await self.show_coord_labels()

        while True:
            # erase the bubble
            await self.draw_bubble(c,0)
            
            # redraw erased parts of frame
            await self.draw_frame()
            
            # get current x,y,z and display
            c = await self.gyro.poll_gyro()
            await self.draw_bubble(c,1)
            await self.show_coord(c)
            
            self.o.show()
            
            if c[2] < 0:
                self.gyro.lock_gyro(False)
                return
    
    # draw frame enclosing bubble
    async def draw_frame(self):
        self.g.circle(32,32,31,1)
        self.g.circle(32,32,17,1)
        self.g.hline(0,32,64,1)
        self.g.vline(32,0,64,1)

    # draw bubble showing tilt
    async def draw_bubble(self,coord,color):
        x = coord[0]
        y = coord[1]
        
        if x > 45:
            x = 45
        elif x < -45:
            x = -45
            
        if y > 45:
            y = 45
        elif y < -45:
            y = -45
            
        yc = round(x/45 * 32) + 32
        xc = round(y/45 * 32) + 32
        
        self.g.circle(xc,yc,8,color)
        
        # erase bubble leakage on right side
        self.g.fill_rect(64,0,9,64,0)  
    
    # show x,y,z coordinate labels
    async def show_coord_labels(self):

        self.o.move_to(9,0)
        self.o.putstr("x:")
        
        self.o.move_to(9,1)
        self.o.putstr("y:")
        
        self.o.move_to(9,2)
        self.o.putstr("z:")

        
    # show coordinate values if changed
    async def show_coord(self,c):
        for i in range(3):
            if self.last_c[i] != c[i]:
                self.last_c[i] = c[i]
                self.o.move_to(12,i)
                self.o.putstr("{:d}     ".format(c[i]))
    
