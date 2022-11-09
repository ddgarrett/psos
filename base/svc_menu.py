"""
    Menu Service Class
    
    Display a menu allowing scrolling up and down
    and selection of a menu item.
    
    Messages include:
    1. "menu" - toggles menu mode on and off
    2. "up"   - highlights the menu item above the current
    3. "down" - highlights the menu item below the current
    4. "enter"- selects the current
    
    When in menu mode the LCD is "locked", preventing it from
    displaying any messages passed via MQTT
    
    Parms include:
    1. sub - topic subscribed to, used to pass menu, up, down and enter messages
    3. items - list of menu items and messages to be sent when an item is selected
       [{"item":"Item 1", "topic":"mqtt/topic", "msg":"mqtt message / payload"},...]
    
"""

from psos_svc import PsosService
import uasyncio
import queue

from svc_msg import SvcMsg

# menu buttons
b_menu  = "UL" # upper left button
b_up    = "UR" # upper right button
b_down  = "LR" # lower right button
b_enter = "LL" # lower left button

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self.sub = parms.get_parm("sub")
        self.lcd = parms.get_parm("lcd")
        self.items = parms.get_parm("items")
        
        self.q = queue.Queue()
        self.in_menu = False
        self.item_idx = 0
        
        self.quick = self.get_parm("quick",{})

    async def run(self):
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self.sub,self.q)
        msg = SvcMsg()
        
        self.lcd = self.get_svc(self.lcd)
        
        while True:
            data = await self.q.get()
            msg.load_subscr(data)
            await self.execute(mqtt,msg)
            
            
    # execute a given command received via MQTT
    async def execute(self,mqtt,msg):

        cmd = msg.get_payload()
        
        if not self.in_menu:
            if cmd == b_menu:
                await self.init_menu()
            else:
                if cmd in self.quick:
                    actions = self.quick[cmd]
                    await self.exec_actions(actions,"done")
        else:
            if cmd == b_up:
                await self.scroll_menu(cmd)
            elif cmd == b_down:
                await self.scroll_menu(cmd)
            elif cmd == b_enter:
                await self.select_item()
            elif cmd == b_menu:
                await self.exit_menu()
            else:
                print("command ignored:",cmd)
            

        # await mqtt.publish(self._pub_topic,out_t)

    async def init_menu(self):
        self.in_menu = True
        self.item_idx = 0
        self.lock_lcd()
        self.display_menu()
        self.save_timeout = self.lcd.get_timeout()
        self.lcd.set_timeout(0)

    async def scroll_menu(self,cmd):
        if cmd == b_down:
            self.item_idx = self.item_idx + 1
            if self.item_idx >= len(self.items):
                self.item_idx = 0
        else:
            self.item_idx = self.item_idx - 1
            if self.item_idx < 0:
                self.item_idx = len(self.items) - 1
                
        self.display_menu()
        
    async def select_item(self):
        item = self.items[self.item_idx]
        if "a" in item:
            actions = item["a"]
            await self.exec_actions(item["a"],item["item"])                        
                        
    async def exec_actions(self,act,exit_msg):               
        for a in act:
            if "a" in a:
                if a["a"] == "pub":
                    p = ""
                    m = ""
                    if "p" in a:
                        p = a["p"]
                    if "m" in a:
                        m = a["m"]
                        
                    await self.get_mqtt().publish(p,m)
                    
                elif a["a"] == "exit":
                    m=exit_msg
                    if "m" in a:
                        m = a["m"]
                    await self.exit_menu(m=m)
                    
                elif a["a"] == "msg":
                    m = exit_msg
                    if "m" in a:
                        m = a["m"]
                    self.update_lcd(m)                    
                    

    async def exit_menu(self,m=None):
        self.in_menu = False
        self.unlock_lcd()
        self.lcd.set_timeout(self.save_timeout)
        if m == None:
            m = "exiting menu..."
            
        self.update_lcd(m)
        
    def lock_lcd(self):
        self.lcd.set_lock(True)
        
    def unlock_lcd(self):
        self.lcd.set_lock(False)
        
    def display_menu(self):
        msg = ""
        for i in range(4):
            idx = self.item_idx + i
            if idx >= len(self.items):
                if i >= len(self.items):
                    break
                idx = idx - len(self.items)
                
            msg += self.items[idx]["item"]
            
            if i < 3:
                msg += "\n"
                
        self.update_lcd(msg)
                
                
    def update_lcd(self,msg):
        msg = SvcMsg(payload=["clear",{"msg":msg}])
        self.lcd.process_msg(msg)

    
    
