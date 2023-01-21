'''
    Display Touch Menu
    
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

# Button Class
class Button():
    def __init__(self, panel,x,y,title_1,title_2):
        super().__init__()
        self.panel = panel
        self.x = x
        self.y = y
        self.title_1 = title_1
        self.title_2 = title_2
        self.height = 40
        self.width  = 80
        self.selected = False
    
    
# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)

        self.svc_dsp = self.get_svc("dsp")
        self.svc_touch = self.get_svc("touch")
        
        self.butns = [
            Button(0,0,0,"Button","One"),
            Button(0,80,0,"Button","Two"),
            Button(1,0,79,"Button","Three"),
            Button(1,80,0,"Button","Four"),
            Button(2,0,0,"Button","Five"),
            Button(2,0,0,"Button","Six"),
            Button(0,0,0,"Button","Seven"),
            Button(0,0,0,"Button","Eight"),
            Button(1,0,0,"Button","Nine"),
            Button(1,0,0,"Button","Ten"),
            Button(2,0,0,"Button","Eleven"),
            Button(2,0,0,"Button","Twelve")
            
        ]
        
        
    async def run(self):
        await self.chk_menu()
        
        
    async def chk_menu(self):
        await self.svc_dsp.lock()
        self.lcd = self.svc_dsp.lcd
        
        for i in range(3):
            self.lcd.fill(clr.BLACK)
            self.lcd.rect(0,0,160,80,clr.CYAN)
            self.lcd.vline(80,0,80,clr.CYAN)
            self.lcd.hline(0,40,160,clr.CYAN)
            
            self.lcd.show_pg(i,3)
            
        self.svc_dsp.unlock()
        
        while True:
            await self.get_touch()
            await uasyncio.sleep_ms(330)
                        
    async def get_touch(self):
        pt_xy = await self.svc_touch.get_touch()
        
        if pt_xy == None:
            return
        
        x_pt = pt_xy[0]
        y_pt = pt_xy[1]
        
        
        panel_x = x_pt//160
        panel_y = y_pt//80
        
        panel_pt_x = x_pt%160
        panel_pt_y = y_pt%80
        
        if panel_y < 3:
            btn = -1
        else:
            btn = 0
            if panel_pt_x >= 80:
                btn = 1
                
            btn = panel_x * 2 + btn
            
            if panel_pt_y >= 40:
              btn = btn+6
              
                        
            await self.svc_dsp.lock()

            await self.blink_btn(panel_x,panel_y,panel_pt_x,panel_pt_y)


            m1 = "pt:({},{})".format(x_pt,y_pt)
            m2 = "panel:({},{})".format(panel_x,panel_y)
            m3 = "ppt:({},{}))".format(panel_pt_x,panel_pt_y)
            m4 = "btn: {}".format(btn)
            
            # await self.blink_btn(btn)
            
            self.lcd.fill(clr.BLACK)
            self.lcd.rect(0,0,160,80,clr.CYAN)
            self.lcd.vline(80,0,80,clr.CYAN)
            self.lcd.hline(0,40,160,clr.CYAN)

            self.lcd.text(m1,6*8,1*16,clr.YELLOW)
            self.lcd.text(m2,6*8,2*16,clr.YELLOW)
            self.lcd.text(m3,6*8,3*16,clr.YELLOW)
            self.lcd.text(m4,6*8,4*16,clr.YELLOW)
            
            self.lcd.show_pg(1,3)
            
                        
            self.svc_dsp.unlock()

            
            
        # self.spi_svc.unlock()
        # self.lcd_locked = False
        
    # render button n
    async def blink_btn(self,panel_x,panel_y,panel_pt_x,panel_pt_y):
        x = 0
        y = 0
        if panel_pt_x >=80:
            x = 80
        if panel_pt_y >= 40:
            y = 40
            
        self.lcd.fill(clr.BLACK)
        self.lcd.fill_rect(x,y,80,40,clr.WHITE)
        self.lcd.rect(0,0,160,80,clr.CYAN)
        self.lcd.vline(80,0,80,clr.CYAN)
        self.lcd.hline(0,40,160,clr.CYAN)
        self.lcd.show_pg(panel_x,panel_y)
        await uasyncio.sleep_ms(330)
        self.lcd.fill(clr.BLACK)
        self.lcd.rect(0,0,160,80,clr.CYAN)
        self.lcd.vline(80,0,80,clr.CYAN)
        self.lcd.hline(0,40,160,clr.CYAN)
        self.lcd.show_pg(panel_x,panel_y)
                

