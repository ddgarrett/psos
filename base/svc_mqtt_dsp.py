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
        
        self.active = False # doesn't startup as active
        self.fltr = None
        
        self.last_displ_row = ("","","")

        
    async def run(self):
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
                self.last_displ_row = ("","","filter changed")
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
            # await self.log("log len before = {}".format(n))
            await self.save_log(n-25)
            self.mqtt_log = self.mqtt_log[(n-25):]
            # await self.log("log len after  = {}".format(len(self.mqtt_log)))

    async def save_log(self,n):
        fn = self.get_parm("save_fn",None)
        if fn != None:
            await self.svc_dsp.lock()
            with open(fn, "a") as myfile:
                for i in range(n):
                    line = "{0}\t{1}\t{2}\t{3}".format(*self.mqtt_log[i])
                    myfile.write(line)
                    myfile.write("\n")
                    
            self.svc_dsp.unlock()
            
    async def show_msg(self,data):
        topic = psos_util.to_str(data[1])
        payload = psos_util.to_str(data[2]).replace("\n","↵")
        t = time.localtime(time.mktime(time.localtime())+self.tz*3600)
        
        t = ("{1}/{2}/{0}".format(*t),"{3}:{4:02d}:{5:02d}".format(*t),topic,payload) # (time,topic,payload)
        self.mqtt_log.append(t)
        
        # we build the log of messages but may wait to show them
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
        for i in range(len(self.mqtt_log)-1,-1,-1):
            row = self.mqtt_log[i]
            filter_split = row[1].split('/')
            if self.fltr.filter_match(filter_split):
                log.insert(0,row)
                if len(log) == 15:
                    break
        # if filtered results didn't change anything,
        # don't display the results
        if len(log) == 0:
            last_row = ("","","empty")
        else:
            last_row = log[len(log)-1]
 
        if self.last_displ_row == last_row:
            return
        
        self.last_displ_row = last_row
        await self.show_log(log)

    async def show_log(self,mqtt_log):
        await self.svc_dsp.lock()
        self.lcd = self.svc_dsp.lcd
        
        log_len = len(mqtt_log)
        first_row_idx = max((log_len-15),0) # row idx >= 0
        
        for p_row in range(3):         # for each panel row
            r_idx = first_row_idx + (p_row * 5)
            for p_col in range(3):        # for each panel column
                self.lcd.fill(clr.BLACK)      # init panel
                char_idx = p_col * 20         # 20 char wide panel 
                for j in range(5):            # 5 lines per panel
                    i = r_idx+j
                    if i < log_len:
                        line = "{1} {2} {3}".format(*mqtt_log[i]) # (time,topic,payload)
                        if len(line) > char_idx:
                            self.lcd.text(line[char_idx:],0,j*16,clr.WHITE)

                # show the panel at x,y = p_col,p_row
                self.lcd.show_pg(p_col,p_row)
                
                # give other tasks a chance to run
                await uasyncio.sleep_ms(0)
        
        self.svc_dsp.unlock()
                
        
