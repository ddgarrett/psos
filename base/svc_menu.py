"""
    Menu Service Class
    
    Display a menu allowing scrolling up and down
    and selection of a menu item.
    
    Messages include:
    1. "enter"- enters menu, submenu or executes menu item
    2. "up"   - highlights the menu item above the current
    3. "down" - highlights the menu item below the current
    4. "exit" - exits the current display or turns on the display
    
    When in menu mode the LCD is "locked", preventing it from
    displaying any messages passed via MQTT
    
"""

from psos_svc import PsosService
from psos_parms import PsosParms
import uasyncio
import queue
import ujson
import psos_util

from svc_msg import SvcMsg

# input message values
m_enter = "enter" # enter menu, submenu, or execute item
m_up    = "up"    # scroll up list, or execute associated quick command 
m_down  = "down"  # scroll down list or execute associate quick command
m_exit  = "exit"  # exit menu or turn on display

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self.sub = parms["sub"] # subscribe topic
        self.menu = parms["menu"]
         
        self.q = queue.Queue()
        self.in_menu = False
        self.item_idx = 0
        self.state = []
        
        # self.quick = self.get_parm("quick",{})
        
        # builtin commands defined at the endof this module
        self.cmd_bi = {
                "redisplay": self.cmd_redisplay,
                "back": self.cmd_back,
                "exit": self.cmd_exit,
                "pub" : self.cmd_pub,
                "msg" : self.cmd_msg,
                "submenu": self.cmd_submenu
            }

    async def run(self):
        
        self.get_svc_lcd() # make sure we have this.svc_lcd set
        
        if type(self.menu) == str:
            c = self._parms.get_config()
            self.menu = psos_util.load_parms(c,self.menu)
            
        main = self.menu["main"]
        self.quick = main["quick"]
        self.items = main["menu"]
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self.sub,self.q)
        msg = SvcMsg()
        
        while True:
            data = await self.q.get()
            msg.load_subscr(data)
            await self.execute(mqtt,msg)
        
    # execute a given command received via MQTT
    async def execute(self,mqtt,msg):

        mp = msg.get_payload()
        
        if not self.in_menu:
            if mp == m_enter:
                await self.init_menu()
            else:
                if mp in self.quick:
                    cmd = self.quick[mp]
                    await self.exec_cmds(cmd,"done")
        else:
            if mp == m_up:
                await self.scroll_menu(mp)
            elif mp == m_down:
                await self.scroll_menu(mp)
            elif mp == m_exit:
                # go to parent menu if it exists
                await self.pop_menu() 
            elif mp == m_enter:
                await self.select_item()
            else:
                print("message ignored:",mp)

    async def init_menu(self):
        self.in_menu = True
        self.item_idx = 0
        self.lock_lcd()
        self.display_menu()
        self.save_timeout = self.svc_lcd.get_timeout()
        self.svc_lcd.set_timeout(0)

    async def exit_menu(self,msg=None):
        
        # Are we running a submenu?
        # Just redisplay previous menu before submenu
        if len(self.state) > 0:
            state = self.state[0]
            self.items    = state["items"]
            self.item_idx = state["idx"]        
        
        # exit menu service
        self.in_menu  = False
        self.item_idx = 0
        self.unlock_lcd()
        self.svc_lcd.set_timeout(self.save_timeout)
        if msg == None:
            msg = " "
            
        self.update_lcd(msg)
    
    # If in a submenu, pop the state of the previous menu
    # and display it.
    # If not in submenu, exit the menu
    async def pop_menu(self,msg=None):
        
        if len(self.state) > 0:
            state = self.state.pop()
            self.items    = state["items"]
            self.item_idx = state["idx"]
            self.display_menu()
            return
        
        await self.exit_menu(msg=msg)

    async def scroll_menu(self,cmd):
        if cmd == m_down:
            self.item_idx = self.item_idx + 1
            if self.item_idx >= len(self.items):
                self.item_idx = 0
        else:
            self.item_idx = self.item_idx - 1
            if self.item_idx < 0:
                self.item_idx = len(self.items) - 1
                
        self.display_menu()
        
    # execute commands for currently selected item
    async def select_item(self):
        item = self.items[self.item_idx]
        if "cmds" in item:
            cmds = item["cmds"]
            await self.exec_cmds(cmds,item["item"])                        
                        
    # execute a list of commands
    # each command consists of a command and additional parameters
    async def exec_cmds(self,cmds,exit_msg):               
        for action in cmds:
            if "cmd" in action:
                # create the psos parms for the command
                parms = PsosParms(action,self.get_defaults(),self.get_config())
                
                cmd = action["cmd"]
                
                # is command one of the builtin commands?
                if cmd in self.cmd_bi:
                    await self.cmd_bi[cmd](exit_msg,parms)
                else:
                    await self.exec_cmd(exit_msg,parms)
                            
        
    # display a list of menu items
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
                
    # display a message after clearing the display
    def update_lcd(self,msg):
        msg = SvcMsg(payload=["clear",{"msg":msg}])
        self.svc_lcd.process_msg(msg)
        
        
    # Execute a dynamic command.
    # Assumes a command is in parms["cmd"]
    # and that there is a module named parms["cmd"].
    # Commands are another type of service but unlike the
    # services created during startup, are expected to have a
    # limited run then exit.
    async def exec_cmd(self,exit_msg,parms):
        
        # add exit message, command name and menu object to parms
        parms["exit_msg"]  = exit_msg
        parms["name"]      = parms["cmd"]
        parms["menu"]      = self
        
        # create the psos parms for the command
        # NOW passed a PsosParms object in parms
        # psos_parms = PsosParms(parms,self._parms._defaults,self.get_config())

        # create a new instance of the Command
        # to implement the command
        module_name = parms["cmd"]
        module      = __import__(module_name)
        command     = module.ModuleService(parms)
        
        command.svc_lcd = self.svc_lcd
        
        # start the command running
        # uasyncio.create_task(command.run())
        # await execution of command instead of starting it?
        await command.run()  

     ############### Builtin Commands ################
                    
    async def cmd_pub(self,exit_msg,parms):
        pub = ""
        msg = ""
        if "pub" in parms:
            pub = parms["pub"]
        if "msg" in parms:
            msg = parms["msg"]
            
        await self.get_mqtt().publish(pub,msg)
        
    # redisplay current menu
    async def cmd_redisplay(self,exit_msg,parms):
        if "wait" in parms:
            await uasyncio.sleep(parms["wait"])
            
        self.display_menu()        
        
        
    # return to previous menu
    # after waiting optional number of seconds
    async def cmd_back(self,exit_msg,parms):
        msg=exit_msg
        if "msg" in parms:
            msg = parms["msg"]
            
        if "wait" in parms:
            await uasyncio.sleep(parms["wait"])
            
        await self.pop_menu(msg=msg)        

    async def cmd_exit(self,exit_msg,parms):
        msg=exit_msg
        if "msg" in parms:
            msg = parms["msg"]
        await self.exit_menu(msg=msg)        

    async def cmd_msg(self,exit_msg,parms):
        msg = exit_msg
        if "msg" in parms:
            msg = parms["msg"]
        self.update_lcd(msg)
        
    async def cmd_submenu(self,exit_msg,parms):
        
        if "name" in parms:
            submenu_name = parms["name"]
            submenu  = self.menu[submenu_name]
    
            # change my menu items to the submenu menu items
            # then display that new menu
            self.state.append({"items":self.items,"idx":self.item_idx})
            self.item_idx = 0
            self.items = submenu["menu"]
            self.display_menu()
        

    #########################################
   
    
