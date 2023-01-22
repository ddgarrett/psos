'''
    Display Touch Menu
    
'''

from psos_svc import PsosService
import uasyncio
import queue
import time

from svc_msg import SvcMsg
import psos_util

from psos_menu_btn import Button
from lcd_3inch5 import LCD
import color_brg_556 as clr

lcd_width = const(480)
lcd_height = const(320)

panel_width = const(160)
panel_height = const(80)

col_cnt = lcd_width/panel_width   # number of panel columns
row_cnt = lcd_height/panel_height # number of panel rows
        
# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self.svc_dsp = self.get_svc("dsp")
        self.svc_touch = self.get_svc("touch")
        lcd = self.svc_dsp.lcd
        self.lcd = lcd
        
        self.butns = [
            Button(lcd,0,0,0,[],select=True),
            Button(lcd,0,80,0,[]),
            Button(lcd,1,0,0,[]),
            Button(lcd,1,80,0,[]),
            Button(lcd,2,0,0,[]),
            Button(lcd,2,80,0,[]),
            
            Button(lcd,0,0,40,[],select=True),
            Button(lcd,0,80,40,[]),
            Button(lcd,1,0,40,[]),
            Button(lcd,1,80,40,[]),
            Button(lcd,2,0,40,[]),
            Button(lcd,2,80,40,[])
        ]

    async def run(self):
        mqtt = self.get_mqtt()
        q = queue.Queue()
        m = SvcMsg()
        await mqtt.subscribe(self.get_parm("sub"),q)
        
        self.svc_dsp = self.get_svc("dsp")
        self.lcd = self.svc_dsp.lcd
        self.init_main_menu()
        
        await self.render_btns() 

        while True:
            data = await q.get()
            m.load_subscr(data)
            await self.check_menu(m.get_payload())
        
    def init_main_menu(self):
        self.menu = self.get_parm("menu")
        if type(self.menu) == str:
            c = self._parms.get_config()
            self.menu = psos_util.load_parms(c,self.menu)
            
        main_menu = self.menu["menu"]

        for i in range(len(main_menu)):
            n = main_menu[i]["name"]
            if type(n) == str:
                n = [n]
            
            self.butns[i].title = n
            
        submenu = main_menu[0]["submenu"]
        submenu = self.menu[submenu]
        for i in range(len(submenu)):
            n = submenu[i]["name"]
            if type(n) == str:
                n = [n]
                
            self.butns[i+6].title = n
            
    # render the buttons for a single panel
    async def render_btns(self):
        await self.svc_dsp.lock()
        for panel in range(3):
            self.lcd.fill(clr.BLACK)
            
            for b in self.butns:
                if b.panel == panel:
                    b.render()
            
            self.lcd.show_pg(panel,3)
            
            # give other tasks a chance to run
            await uasyncio.sleep_ms(0)
            
        self.svc_dsp.unlock()
        
    # selects menu button based on MQTT msg
    async def check_menu(self,msg):
        x_pt = msg["x"]
        y_pt = msg["y"]
        
        panel_x = x_pt//160
        panel_y = y_pt//80
        
        panel_pt_x = x_pt%160
        panel_pt_y = y_pt%80
        
        if panel_y < 3:
            return

        btn = 0
        if panel_pt_x >= 80:
            btn = 1
            
        btn = panel_x * 2 + btn
        
        if panel_pt_y >= 40:
          btn = btn+6
                    
        if btn < 6:
            for b in self.butns:
                b.select = False
            self.butns[btn].select = True
            self.butns[6].select = True
            
        else:
            for b in range(6):
                i = b+6
                if i == btn:
                    self.butns[i].select = True
                else:
                    self.butns[i].select = False
            
        await self.render_btns()
