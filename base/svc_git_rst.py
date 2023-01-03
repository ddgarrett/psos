"""
    Update from Git Service Class - Part 1
    
    Update config.json to start with a special device name
    that will run the Upate Git Part 2 process.
    
    Then restart the microcontroller to run the update process.
    
    Triggered by any message to it's subscribed topic.
    
"""

from psos_svc import PsosService
import uasyncio
import queue
import urequests
import gc
import os

import psos_util
from svc_msg import SvcMsg

import secrets
import ujson

class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        self.q = queue.Queue()
        self.sub       = self.get_parm("sub",None)
        self.upd_parms = self.get_parm("upd_parms","git_oled_upd_parms.json")
  
    
    async def run(self):
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self.sub,self.q)
        
        while True:
            await self.q.get()
            await self.prep_upd()
            await self.log("restarting for git pull")
            self.reset(rsn="git pull")
                   
    # prepare for restart that runs an update
    # simpy update config to use different parms
    async def prep_upd(self):
        config = self.get_parm("config")
        # config["o_device"] = config["device"]
        # config["device"] = self.upd_dev
        config["o_fn_parms"] = config["fn_parms"]
        config["fn_parms"]   = self.upd_parms
        self.save_json("config.json",config)
    
    # save object o to file named "fn"
    def save_json(self,fn,o):
        with open(fn, "w") as f:
            ujson.dump(o, f)

