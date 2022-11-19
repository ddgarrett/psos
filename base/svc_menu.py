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
from psos_parms import PsosParms
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
        
        # builtin commands defined at the endof this module
        self.cmd_bi = {
                "exit": self.cmd_exit,
                "pub" : self.cmd_pub,
                "msg" : self.cmd_msg
            }

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
                await self.exit_menu()
            elif cmd == b_menu:
                await self.select_item()
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
            await self.exec_actions(actions,item["item"])                        
                        
    # execute a list of commands
    # each command consists of an action and additional parameters
    async def exec_actions(self,actions,exit_msg):               
        for action in actions:
            if "a" in action:
                cmd = action["a"]
                
                # is command one of the builtin commands?
                if cmd in self.cmd_bi:
                    await self.cmd_bi[cmd](exit_msg,action)
                else:
                    await self.exec_cmd(exit_msg,action)
                    
                            
    async def exit_menu(self,m=None):
        self.in_menu = False
        self.unlock_lcd()
        self.lcd.set_timeout(self.save_timeout)
        if m == None:
            m = " "
            
        self.update_lcd(m)
        
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
        
    # Execute a dynamic command.
    # Assumes a command is in parms["a"]
    # and that there is a module named parms["a"].
    # Commands are another type of service but unlike the
    # services created during startup, are expected to have a
    # limited run then exit.
    async def exec_cmd(self,exit_msg,parms):
        
        # use a copy of my parms for new command parms
        new_parms = self._parms._parms.copy()
        my_defaults = self._parms._defaults
        
        # add exit message and command specific parms to new parms
        new_parms["exit_msg"]  = exit_msg
        new_parms["name"]      = parms["a"]
        new_parms.update(parms)
        
        # create the psos parms for the command
        psos_parms = PsosParms(new_parms,my_defaults)

        # create a new instance of the Command
        # to implement the command
        module_name = parms["a"]
        print("creating command "+module_name)
        module      = __import__(module_name)
        command     = module.ModuleService(psos_parms)
        
        # start the command running
        print("... starting "+module_name)
        uasyncio.create_task(command.run())
        print("... "+module_name+ " running")
        

     ############### Builtin Commands ################
                    
    async def cmd_pub(self,exit_msg,parms):
        p = ""
        m = ""
        if "p" in parms:
            p = parms["p"]
        if "m" in parms:
            m = parms["m"]
            
        await self.get_mqtt().publish(p,m)
        
    async def cmd_exit(self,exit_msg,parms):
        m=exit_msg
        if "m" in parms:
            m = parms["m"]
        await self.exit_menu(m=m)        

    async def cmd_msg(self,exit_msg,parms):
        m = exit_msg
        if "m" in parms:
            m = parms["m"]
        self.update_lcd(m)        

    #########################################
   
    
