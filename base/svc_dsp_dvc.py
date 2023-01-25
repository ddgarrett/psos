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
                self.dvc[y][x] = {} # reuse array for captured data

        
    async def run(self):
        q    = queue.Queue()
        msg  = SvcMsg()
        mqtt = self.get_mqtt()
        
        await mqtt.subscribe("+/dht",q)
        
        # not sure it will work to have two subscriptions to same q?
        await mqtt.subscribe(self.get_parm("sub_cmd"),q)
        
        while True:
            data = await q.get()
        
            # did we receive a command?
            if psos_util.to_str(data[1]) == self.get_parm("sub_cmd"):
                await self.exec_cmd(data[2])
            else:
                msg.load_subscr(data)
                device = await self.save_msg(msg)
                
                if device != None and self.active:
                    await self.show_device(device,True)
        
    # execute a command
    async def exec_cmd(self,cmd):
        if cmd == "start":
            self.active = True
            await uasyncio.sleep_ms(330) # let other messages send
            await self.blank_dsp()
            for dvc in self.dvc_lookup.keys():
                await self.show_device(dvc,False)
                await uasyncio.sleep_ms(0)
                
        elif cmd == "stop":
            self.active = False
        else:
            await self.log("unrecognized command: {}".format(cmd))
    
    # save the data for a message in array.
    async def save_msg(self,data):
        # add time to the payload (dictionary)
        d = data.get_payload()
        t = time.localtime(time.mktime(time.localtime())+self.tz*3600)
        d["time"] = "{3}:{4:02d}:{5:02d}".format(*t)
        
        # add data to a y by x array
        dvc = data._topic.split("/")[0]
        d["dev"] = dvc
        if dvc in self.dvc_lookup:
            (x,y) = self.dvc_lookup[dvc]
            self.dvc[y][x] = d
            return dvc
        
        return None
            
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
    async def show_device(self,dvc,blank_first):
        (x,y) = self.dvc_lookup[dvc]
        data = self.dvc[y][x]

        if blank_first:
            await self.svc_dsp.lock()
            self.lcd = self.svc_dsp.lcd
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
        
        self.write_str("  {} TEMP & HUMID".format(dvc),0,0,clr.YELLOW)
        if "temp" in data:       
            self.write_str("TEMP: {temp}".format(**data),0,1,clr.CYAN)
            self.write_str("HUM: {hum}".format(**data),0,2,clr.CYAN)
            self.write_str("DEV: {dev}".format(**data),0,3,clr.CYAN)
            self.write_str("TIME: {time}".format(**data),0,4,clr.CYAN)

        self.lcd.show_pg(x,y)
        self.svc_dsp.unlock()    
        
    # x,y are character based x and y co-ordinates
    def write_str(self,text,x,y,c):
        px = x*8+4
        py = y*16+4
        if len(text) > 19:
            text = text[:19]
            
        self.lcd.text(text,px,py,c)
