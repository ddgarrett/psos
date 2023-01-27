'''
    Display Multiple Devices,
    One per Panel

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

        self.active = False # doesn't startup as active
        
        # initi device lookup and data table
        self.dvc = self.get_parm("dvc") # defines devices and positions
        self.dvc_lookup = {}
        
        for y in range(len(self.dvc)):
            for x in range(len(self.dvc[y])):
                dvc = self.dvc[y][x]
                self.dvc_lookup[dvc] = (x,y)
                self.dvc[y][x] = [{"dev":dvc}]*3# reuse array for captured data
                       
    async def run(self):
        q    = queue.Queue()
        msg  = SvcMsg()
        mqtt = self.get_mqtt()
        
        # list of topics to subscribe to
        subs = self.get_parm("subs")
        
        for sub in subs.values():
            await mqtt.subscribe(sub,q)
            
        # topics I recognize/require
        self.topic_calls = {subs["tch"] :self.handle_touch,
                            subs["cmd"] :self.exec_cmd,
                            subs["temp"]:self.handle_temp,
                            subs["soil"]:self.handle_soil,
                            subs["mem"] :self.handle_mem }

        # current display type: temp, soil or mem
        self.cur_show = "temp"
        
        while True:
            data = await q.get()
            # print("received msg:",data)
            msg.load_subscr(data)
            filter = msg._filter
            
            if filter in self.topic_calls:
                await (self.topic_calls[filter](msg))
            else:
                print("unrecognized filter:",filter)
                await self.log("unrecognized filter: {}".format(filter))
                        
    # handle touch messages
    async def handle_touch(self,msg):
        if not self.active:
            return
        
        # print("touch:",msg._payload)
        x_pt = msg._payload["x"]
        y_pt = msg._payload["y"]
        
        panel_x = x_pt//160
        panel_y = y_pt//80
        
        # touch within a defined panel?
        if panel_y < len(self.dvc) and panel_x < len(self.dvc[panel_y]):
            dev = self.dvc[panel_y][panel_x][0]["dev"]
            
            type = self.cur_show
            if type == "temp":
                type = "dht"
                
            topic = "{}/{}/upd".format(dev,type)
            await self.get_mqtt().publish(topic,"upd")
            
            # blink the selected panel
            await self.show_device(dev,True,invert=True)

    
    # execute a command
    async def exec_cmd(self,msg):
        cmd = msg._payload
        
        # print("svc_dsp_dv received command {}".format(cmd))
        
        if cmd == "start":
            self.active = True
            await uasyncio.sleep_ms(330) # let other messages send
            await self.blank_dsp()
               
        elif cmd == "stop":
            self.active = False
        elif cmd in ("temp","soil","mem"):
            self.cur_show = cmd
            await self.show_all(False)
        else:
            await self.log("unrecognized command: {}".format(cmd))
    
    async def show_all(self,blank_first):
        for y in range(3):
            for x in range(3):
                if len(self.dvc) > y and len(self.dvc[y]) > x:
                    dvc = self.dvc[y][x][0]["dev"]
                    await self.show_device(dvc,blank_first)
                    await uasyncio.sleep_ms(0)
                                          
    # handle temperature messages
    async def handle_temp(self,msg):
        await self.save_msg(msg,"temp")
    
    # handle soile messages
    async def handle_soil(self,msg):
        await self.save_msg(msg,"soil")
    
    # handle memory messages
    async def handle_mem(self,msg):
        await self.save_msg(msg,"mem")
    
    # save the data for a message in array.
    async def save_msg(self,data,data_type):
        data_idx = ["temp","soil","mem"].index(data_type)
        # add time to the payload (dictionary)
        d = data.get_payload()
        t = time.localtime(time.mktime(time.localtime())+self.tz*3600)
        d["time"] = "{3}:{4:02d}:{5:02d}".format(*t)
        
        # add data to a y by x array
        dvc = data._topic.split("/")[0]
        d["dev"] = dvc
        if dvc in self.dvc_lookup:
            (x,y) = self.dvc_lookup[dvc]
            self.dvc[y][x][data_idx] = d
            
            if self.cur_show == data_type and self.active:
                await self.show_device(dvc,True)
            
    # blank out all panels in display region
    async def blank_dsp(self):
        await self.svc_dsp.lock()
        self.lcd = self.svc_dsp.lcd

        for x in range(3):
            for y in range(3):
                self.lcd.fill(clr.BLACK)
                self.lcd.show_pg(x,y)
                
        self.svc_dsp.unlock()    
       
    # show formatted data for a device
    # in specified panel
    async def show_device(self,dvc,blank_first,invert=False):
        (x,y) = self.dvc_lookup[dvc]
        
        data_idx = ["temp","soil","mem"].index(self.cur_show)
        data = self.dvc[y][x][data_idx]

        if blank_first:
            await self.svc_dsp.lock()
            self.lcd = self.svc_dsp.lcd
            if invert:
                self.lcd.fill(~clr.BLACK)
                self.lcd.rect(0,0,160,80,~clr.CYAN)
            else:
                self.lcd.fill(clr.BLACK)
                self.lcd.rect(0,0,160,80,clr.CYAN)
                
            self.lcd.show_pg(x,y)
            self.svc_dsp.unlock()
            await uasyncio.sleep_ms(330)
            
        await self.svc_dsp.lock()
        self.lcd = self.svc_dsp.lcd
        
        # writing a single panel
        self.lcd.fill(clr.BLACK)
        self.lcd.rect(0,0,160,80,clr.CYAN)
        
        f = [self.fmt_temp, self.fmt_soil, self.fmt_mem][data_idx]
        f(dvc,data)
        if "time" in data:
            self.write_str("DEV: {dev}".format(**data),0,3,clr.CYAN)
            self.write_str("TIME: {time}".format(**data),0,4,clr.CYAN)
                
        self.lcd.show_pg(x,y)
        self.svc_dsp.unlock()    
        
    # Data Formatters
    def fmt_temp(self,dvc,data):
        self.write_str("     {} {}".format(dvc,"Temp"),0,0,clr.YELLOW)
        if "temp" in data:       
            self.write_str("TEMP: {temp}".format(**data),0,1,clr.CYAN)
            self.write_str("HUM: {hum}".format(**data),0,2,clr.CYAN)
        
    def fmt_soil(self,dvc,data):
        self.write_str("     {} {}".format(dvc,"Soil"),0,0,clr.YELLOW)
        if "lvl_10" in data:       
            self.write_str("LVL 10:  {lvl_10}".format(**data),0,1,clr.CYAN)
            self.write_str("LVL 100: {lvl_100}".format(**data),0,2,clr.CYAN)
        
    def fmt_mem(self,dvc,data):
        self.write_str("     {} {}".format(dvc,"Memory"),0,0,clr.YELLOW)
        if "mem_free" in data:       
            self.write_str("MEM: {mem_free}".format(**data),0,1,clr.CYAN)
            self.write_str("DSK: {disk_free}".format(**data),0,2,clr.CYAN)
    
    # x,y are character based x and y co-ordinates
    def write_str(self,text,x,y,c):
        px = x*8+4
        py = y*16+4
        if len(text) > 19:
            text = text[:19]
            
        self.lcd.text(text,px,py,c)
