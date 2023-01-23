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
            
        self.btns = [
            Button(0,0,0),
            Button(0,80,0),
            Button(1,0,0),
            Button(1,80,0),
            Button(2,0,0),
            Button(2,80,0),
            
            Button(0,0,40),
            Button(0,80,40),
            Button(1,0,40),
            Button(1,80,40),
            Button(2,0,40),
            Button(2,80,40)
        ]

    async def run(self):
        self.svc_dsp = self.get_svc("dsp")
        self.svc_touch = self.get_svc("touch")
        self.lcd = self.svc_dsp.lcd

        mqtt = self.get_mqtt()
        self.mqtt = mqtt
        q = queue.Queue()
        m = SvcMsg()
        await mqtt.subscribe(self.get_parm("sub"),q)
        
        msg_q = await self.init_main_menu()
        await self.render_btns()
        await uasyncio.sleep_ms(1000) # give other services time to start
        for mq in msg_q:
            await mqtt.publish(mq[0],mq[1])

        while True:
            data = await q.get()
            m.load_subscr(data)
            await self.check_menu(m.get_payload())
        
    async def init_main_menu(self):
        self.menu = self.get_parm("menu")
        if type(self.menu) == str:
            c = self._parms.get_config()
            self.menu = psos_util.load_parms(c,self.menu)
            
        main_menu = self.menu["menu"]

        for i in range(len(main_menu)):
            if i < len(main_menu):
                self.btns[i].set_parms(main_menu[i])
            else:
                self.btns[i].set_parms(None)
                
        if "submenu" in main_menu[0]:
            self.set_submenu(main_menu[0]["submenu"])
            
        # Select First Button of Main Menu and Submenu
        # await uasyncio.sleep_ms(1000) # give other services time to start
        msg_q = []
        await self.btns[0].select_btn(msg_q)
        await self.btns[6].select_btn(msg_q)
        
        return msg_q
            
    # render the buttons for a single panel
    async def render_btns(self):
        await self.svc_dsp.lock()

        for panel in range(3):
            self.lcd.fill(clr.BLACK)
            
            for b in self.btns:
                if b.panel == panel:
                    b.render(self.lcd)
            
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
              
        msg_q = []
        
        if self.btns[btn].selectable():
            if btn < 6:
                for b in self.btns:
                    if b.selected:
                        await b.deselect_btn(msg_q)

                submenu = await self.btns[btn].select_btn(msg_q)
                self.set_submenu(submenu)
                await self.btns[6].select_btn(msg_q)
                
            else:
                for b in range(6):
                    i = b+6
                    if i == btn:
                        await self.btns[i].select_btn(msg_q)
                    else:
                        if self.btns[i].selected: 
                            await self.btns[i].deselect_btn(msg_q)
            
            await self.render_btns()
            
            for m in msg_q:
                await self.mqtt.publish(m[0],m[1])
            
    def set_submenu(self,submenu_name):
        if submenu_name == None or not submenu_name in self.menu:
            for i in range(6,12):
                self.btns[i].set_parms(None)
            return
        
        submenu = self.menu[submenu_name]
        for i in range(6):
            j = i + 6
            if i < len(submenu):
                self.btns[i+6].set_parms(submenu[i])
            else:
                self.btns[i+6].set_parms(None)