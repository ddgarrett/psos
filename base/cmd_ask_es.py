
from psos_svc import PsosService
import uasyncio
import random


# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self.menu = self.get_parm("menu")
        
        gyro  = self.get_parm("gyro","gyro")
        self.gyro = self.get_svc(gyro)
        
        a ='''How should\\nI know?
Go look it up\\n on Google
Why are you\\nasking me?
Beats me
Don't bother\\nme, I'm busy
Why are you\\nasking me?
Yes
No
Maybe
I'm not gonna\\nsay anything\\nanymore, that's\\nit
Stupid
What a pain\\nin the ass
Love you
Stop bothering\\nme'''
        
        self.a = a.split('\n')
        for i in range(len(self.a)):
            self.a[i] = self.a[i].replace('\\n','\n')
            
    async def run(self):
        self.gyro.lock_gyro(True)
        mi = -1
        msg = ""
       
        while True:
            self.menu.update_lcd("Ask a question\nturn upside down\nonce for answer,\ntwice to exit")
            
            while msg != "over":
                r,msg = await self.gyro.poll_chg()
                await uasyncio.sleep_ms(250)

            # make sure answer changes
            prev_mi = mi
            while mi == prev_mi:
                mi = random.randint(1,len(self.a))-1
                
            self.menu.update_lcd(self.a[mi])
            
            # wait for non-over message
            while msg == "over":
                r,msg = await self.gyro.poll_chg(ret_flat=True)
                
            # check for "over" message in next 3 seconds
            i = 0
            while i <= 8:
                i += 1
                r,msg = await self.gyro.poll_chg(ret_flat=True)
                if msg == "over":
                    self.gyro.lock_gyro(False)
                    return
    
