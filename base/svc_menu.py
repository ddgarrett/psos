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
        
        self.sub = parms.get_parm("sub")
        self.lcd = parms.get_parm("lcd")
        self.menu = parms.get_parm("menu")
        # self.items = parms.get_parm("items")
        
        self.q = queue.Queue()
        self.in_menu = False
        self.item_idx = 0
        self.state = []
        
        # self.quick = self.get_parm("quick",{})
        
        # builtin commands defined at the endof this module
        self.cmd_bi = {
                "exit": self.cmd_exit,
                "pub" : self.cmd_pub,
                "msg" : self.cmd_msg,
                "submenu": self.cmd_submenu
            }

    async def run(self):
        
        self.menu = self.parse_menu(self.menu)
        main = self.menu["main"]
        self.quick = main["quick"]
        self.items = main["menu"]
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self.sub,self.q)
        msg = SvcMsg()
        
        self.lcd = self.get_svc(self.lcd)
        
        while True:
            data = await self.q.get()
            msg.load_subscr(data)
            await self.execute(mqtt,msg)
            
    def parse_menu(self,fn):
        # read the paramter file
        with open(fn) as f:
            parms = ujson.load(f)
            f.close()
            return parms
        
        return None
        
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
        self.save_timeout = self.lcd.get_timeout()
        self.lcd.set_timeout(0)

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
        self.lcd.set_timeout(self.save_timeout)
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
                cmd = action["cmd"]
                
                # is command one of the builtin commands?
                if cmd in self.cmd_bi:
                    await self.cmd_bi[cmd](exit_msg,action)
                else:
                    await self.exec_cmd(exit_msg,action)
                            
        
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
        self.lcd.process_msg(msg)
        
        
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
        psos_parms = PsosParms(parms,self._parms._defaults)

        # create a new instance of the Command
        # to implement the command
        module_name = parms["cmd"]
        print("creating command "+module_name)
        module      = __import__(module_name)
        command     = module.ModuleService(psos_parms)
        
        # start the command running
        print("... starting "+module_name)
        uasyncio.create_task(command.run())
        print("... "+module_name+ " running")
        

     ############### Builtin Commands ################
                    
    async def cmd_pub(self,exit_msg,parms):
        pub = ""
        msg = ""
        if "pub" in parms:
            pub = parms["pub"]
        if "msg" in parms:
            msg = parms["msg"]
            
        await self.get_mqtt().publish(pub,msg)
        
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
   
    
