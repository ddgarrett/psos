'''
    Display MQTT Messages

'''

from psos_svc import PsosService
import uasyncio
import queue
import time

from svc_msg import SvcMsg
import psos_util

from lcd_3inch5 import LCD
import color_brg_556 as clr

from psos_subscription import Subscription

import gc

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

        self.svc_dsp = self.get_svc("dsp")

        self.mqtt_log = [] # [""]*20
        self.curr_pos = 0
        
        self.active = False # doesn't startup as active
        self.fltr = None
        
        # self.lcd_locked = False
        
    async def run(self):
        self.svc_menu = self.get_svc("menu")
        self.menu_item = 0

        q    = queue.Queue()
        msg  = SvcMsg()
        mqtt = self.get_mqtt()
        
        await mqtt.subscribe("#",q)
        
        while True:
            data = await q.get()
        
            # did we receive a command?
            if psos_util.to_str(data[1]) == self.get_parm("sub_cmd"):
                await self.exec_cmd(data[2])
            # did we receive a filter?
            elif psos_util.to_str(data[1]) == self.get_parm("sub_fltr"):
                await self.set_filter(data[2])
                
            await self.show_msg(data)

            if len(self.mqtt_log) > self.get_parm("max_log",250):
                await self.free_mem()
                
            gc.collect()
                
    # execute a command
    async def exec_cmd(self,cmd):
        if cmd == "free":
            await self.free_mem()
        elif cmd == "start":
            self.active = True
        elif cmd == "stop":
            self.active = False
        else:
            await self.log("unrecognized command: {}".format(cmd))
    
    # create a filter
    async def set_filter(self,fltr):
        if fltr == "#":
            self.fltr = None
        else:
            # don't actually subscribe
            # just use this to select messages for display
            self.fltr = Subscription(fltr,None,0)
    
    async def free_mem(self):
        n = len(self.mqtt_log)
        if n > 30:
            await self.log("log len before = {}".format(n))
            self.mqtt_log = self.mqtt_log[(n-25):]
            await self.log("log len after  = {}".format(len(self.mqtt_log)))

    async def show_msg(self,data):
        topic = psos_util.to_str(data[1])
        payload = psos_util.to_str(data[2])
        t = time.localtime(time.mktime(time.localtime())+self.tz*3600)
        
        t = (t[3],t[4],t[5],topic,payload)
        msg = "{0}:{1:02d}:{2:02d} {3} {4}".format(*t)
        self.mqtt_log.append((msg,topic.split("/")))
        
        '''  TODO: allow other services to take over display
        if self.svc_dsp.curr_svc != self._name:
            return
        '''
        '''
        if not self.svc_menu.butns[self.menu_item].select:
            return
        '''
        # we build the log of messages but wait to show them
        # until we are active
        if not self.active:
            return
        
        if self.fltr == None:
            await self.show_log(self.mqtt_log)
        else:
            await self.show_filtered()
            
    # show only those rows which meet filter criteria
    # Build a log of filtered results up to the maximum (15) then
    # pass to show_log
    async def show_filtered(self):
        log = []
        first_row = 15
        for i in range(len(self.mqtt_log)-1,-1,-1):
            row = self.mqtt_log[i]
            if self.fltr.filter_match(row[1]):
                log.insert(0,row)
                if len(log) == 15:
                    break
                
        await self.show_log(log)

    async def show_log(self,mqtt_log):
        await self.svc_dsp.lock()
        self.lcd = self.svc_dsp.lcd
        
        log_len = len(mqtt_log)
        first_row_idx = log_len - 15
        if first_row_idx < 0:
            first_row_idx = 0
        
        for p_row in range(3):         # for each panel row
            r_idx = first_row_idx + (p_row * 5)
            for p_col in range(3):                    # for each panel column
                self.lcd.fill(clr.BLACK)                  # init panel
                char_idx = p_col * 20     # 20 char per panel column
                for j in range(5):        # 5 lines per panel
                    i = r_idx+j
                    if i < log_len:
                        line = mqtt_log[i][0]
                        if len(line) > char_idx:
                            self.lcd.text(line[char_idx:],0,j*16,clr.WHITE)

                # show the panel at x,y = p_col,p_row
                self.lcd.show_pg(p_col,p_row)
                
                # give other tasks a chance to run
                await uasyncio.sleep_ms(0)
        
        self.svc_dsp.unlock()
                
        
