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

        # spi_svc = parms.get_parm("spi")
        # self.spi_svc = self.get_svc(spi_svc)
        # spi = self.spi_svc.get_spi()
        
        self.svc_dsp = self.get_svc("dsp")
        self.svc_touch = self.get_svc("touch")

        # self.lcd = LCD(self.spi_svc,panel_width,panel_height)
                
        # self.mqtt_log = [""]*20
        # self.curr_pos = 0
        
        # self.lcd_locked = False
        
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
        '''
        q    = queue.Queue()
        msg  = SvcMsg()
        mqtt = self.get_mqtt()
        
        
        await mqtt.subscribe("#",q)
        '''
        await self.chk_menu()
        
        # self.menu_task = uasyncio.create_task(self.chk_menu())
        
        '''
        while True:
            data = await q.get()
            try:
                await self.show_msg(data)
                
                # was this device sent a "free" message?
                if psos_util.to_str(data[1]) == self.get_parm("sub_free"):
                    await self.free_mem()
                    
                if len(self.mqtt_log) > self.get_parm("max_log",250):
                    await self.free_mem()
                    
            except Exception as e:
                print("exception",str(e))
                print("data:",data)
            
    async def free_mem(self):
        n = len(self.mqtt_log)
        if n > 30:
            await self.log("log len before = {}".format(n))
            self.mqtt_log = self.mqtt_log[(n-25):]
            await self.log("log len after  = {}".format(len(self.mqtt_log)))

    async def show_msg(self,data):
        # print("received",msg)
        
        topic = psos_util.to_str(data[1])
        payload = psos_util.to_str(data[2])
        t = time.localtime(time.mktime(time.localtime())+self.tz*3600)
        
        t = (t[3],t[4],t[5],topic,payload)
        msg = "{0}:{1:02d}:{2:02d} {3} {4}".format(*t)
        self.mqtt_log.append(msg)
        
        await self.svc_dsp.lock()
        self.lcd = self.svc_dsp.lcd
        
        first_row_idx = len(self.mqtt_log) - 15
        
        for p_row in range(3):         # for each panel row
            r_idx = first_row_idx + (p_row * 5)
            for p_col in range(3):                    # for each panel column
                self.lcd.fill(clr.BLACK)                  # init panel
                char_idx = p_col * 20     # 20 char per panel column
                for j in range(5):        # 5 lines per panel
                    line = self.mqtt_log[r_idx+j]
                    # self.lcd.text("x",0,j*16,clr.WHITE)
                    if len(line) > char_idx:
                        self.lcd.text(line[char_idx:],0,j*16,clr.WHITE)

                # show the panel at x,y = p_col,p_row
                self.lcd.show_pg(p_col,p_row)
        
        self.svc_dsp.unlock()
        # self.spi_svc.unlock()
        # self.lcd_locked = False
        '''
        
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
        
        '''
        # todo: make these a parm and customization value
        x_min = 385  # x = 0
        x_max = 3809 # x=480
        x_range = x_max - x_min
        
        y_min = 451  # y=320
        y_max = 3504 # y=0
        y_range = y_max - y_min
        
        # may have to wait for a lock on the SPI
        get = await self.lcd.touch_get()
    
        # print(get)
        if get != None and get[0] != 0 and get[1] != 0:
            await self.spi_svc.lock() # self.lcd_locked = True
            
            # self.lcd.write_cmd(0x20) # invert
            x = get[0]
            x = min(x_max,x)
            x = max(x_min,x)
            x_pt = round((x-x_min)/x_range*480)
            
            y = get[1]
            y = min(y_max,y)
            y = max(y_min,y)
            y_pt = round((1-(y-y_min)/y_range)*320)
            '''
        
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
                

