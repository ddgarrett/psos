'''
    Test the 3.5" LCD Driver lcd_3inch5

'''

from psos_svc import PsosService
import uasyncio
import queue

from svc_msg import SvcMsg

from lcd_3inch5 import LCD
import color_brg_556 as clr

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self.w = 160 # width and height of each panel
        self.h = 80

        self.c = int(480/self.w) # number of columns and rows in complete LCD
        self.r = int(320/self.h)

        self.lcd = LCD(self.w,self.h)
        
        self.p = (0,0)
        self.x = 0
        self.y = 0
        
        
    async def run(self):
        q    = queue.Queue()
        msg  = SvcMsg()
        mqtt = self.get_mqtt()
        
        await mqtt.subscribe(self.get_parm("sub"),q)
        
        while True:
            data = await q.get()
            try:
                msg.load_subscr(data)
                await self.run_test(msg.get_payload())
            except Exception as e:
                print("exception",str(e))
                print("data:",data)
            
    async def run_test(self,p):
        print("received",p)
        
        if type(p) == list:
            for cmd in p:
                if type(cmd) == list and len(cmd) > 0:
                    cmd_val = cmd[0]
                    
                    if (cmd_val == "p" and len(cmd) > 1 and
                        type(cmd[1]) == list and len(cmd[1]) == 2):
                        self.p = cmd[1]
                        self.lcd.fill(clr.BLACK) # also clear screen
                        
                    elif cmd_val == "msg" and len(cmd) > 1 and type(cmd[1]) == str:
                        self.lcd.text(cmd[1],4,4,clr.YELLOW)
                        
            self.lcd.rect(0,0,self.w,self.h,clr.WHITE)
            self.lcd.rect(1,1,self.w-2,self.h-2,clr.BLACK)
            self.lcd.rect(2,2,self.w-4,self.h-4,clr.BLACK)
            self.lcd.show_pg(self.p[0],self.p[1])
                        
                        
                        
                

