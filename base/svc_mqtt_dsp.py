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

        self.mqtt_log = [] 
        
        self.active = False # doesn't startup as active
        self.fltr_str = "#"
        self.fltr = self.fltr = Subscription("#",None,0)
        
        #self.last_displ_row = ("","","")
        self.last_row_idx = -1
        self.need_refresh = True
        
        self.print_stats = self.get_parm("print_stats",False)
        
    async def run(self):
        q    = queue.Queue()
        msg  = SvcMsg()
        
        # receive via MQTT LOG instead of directly from MQTT
        # This will allow us to index through disk version of log
        mqtt = self.get_parm("mqtt_log",None)
        self.mqtt = self.get_svc(mqtt)
        await self.mqtt.subscribe("#",q)
        
        while True:
            data = await q.get()
            
            # did we receive a command?
            if psos_util.to_str(data[1]) == self.get_parm("sub_cmd"):
                await self.exec_cmd(data[2])
                
            # did we receive a filter?
            elif psos_util.to_str(data[1]) == self.get_parm("sub_fltr"):
                # self.last_displ_row = ("","","filter changed")
                await self.set_filter(data[2])
        
            await self.show_msg(data)
            
            gc.collect()
                
    # execute a command
    async def exec_cmd(self,cmd):
        if cmd == "start":
            self.active = True
            self.need_refresh = True
        elif cmd == "stop":
            self.active = False
            self.need_refresh = True
        else:
            await self.log("unrecognized command: {}".format(cmd))
    
    # create a filter
    async def set_filter(self,fltr):        
        if fltr != self.fltr_str:
            self.fltr_str = fltr
            self.fltr = Subscription(fltr,None,0)
            self.mqtt_log = []
            self.last_row_idx = -1
    
    
    # Add Data to Array to be displayed
    async def show_msg(self,data):
        if not self.active:
            return

        log = self.mqtt_log
        
        log_file_len = await self.mqtt.log_len()
        insert_pos = len(log)
        
        cnt = 0
        b_cnt = 0
        
        t1 = time.ticks_ms()
        
        # read backwards through log file entries
        for i in range(log_file_len-1,-1,-1):
            # reached previously read data?
            if self.last_row_idx == i:
                break
            
            # new row match filter?
            row = await self.mqtt.read_log_entry(i)
            cnt += 1
            b_cnt = b_cnt + len(row)+1+4
            row = row.split("\t")    
            filter_split = row[2].split('/')
            if self.fltr.filter_match(filter_split):
                
                # add row to end
                log.insert(insert_pos,(i,row))
                self.need_refresh = True

                # more rows than we need?
                if len(log) > 15:
                    del log[0]
                    insert_pos = insert_pos -1
                    if insert_pos < 0:
                        break
                    
            # give other tasks a chance to run every 10th record
            # based on some timings, that's ~1/3 second
            if cnt%10 == 0:
                await uasyncio.sleep_ms(0)
            
        if self.print_stats:
            interval = time.ticks_diff(time.ticks_ms(),t1)
            self.last_row_idx = log_file_len - 1
            # print("read {} records from disk in {}ms, last row idx={}".format(cnt,interval,self.last_row_idx))
            if interval > 0:
                print("In {:.3f} sec, read {} recs @ {:.0f}recs/sec, {} bytes @ {:.0f}bytes/sec".format(interval/1000,cnt,cnt/interval*1000,b_cnt,b_cnt/interval*1000))
            else:
                print(" 0 seconds, read {} recs".format(cnt))

        #t1 = time.ticks_ms()
        if self.need_refresh:
            await self.show_log(log)
            self.need_refresh = False
            
        # interval = time.ticks_diff(time.ticks_ms(),t1)
        # print("... {}ms to display data".format(interval))

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
                        row = mqtt_log[i] # data is in second position
                        row = row[1]
                        line = "{1} {2} {3}".format(*row) # (time,topic,payload)
                        # line = "{} {}".format(mqtt_log[i][0],line)
                        if len(line) > char_idx:
                            self.lcd.text(line[char_idx:],0,j*16,clr.WHITE)

                # show the panel at x,y = p_col,p_row
                self.lcd.show_pg(p_col,p_row)
                
                # give other tasks a chance to run
                await uasyncio.sleep_ms(0)
        
        self.svc_dsp.unlock()
