"""
    PSOS Service Class
    
    Superclass of all PSOS Services
    
"""

import uasyncio
import ujson

import machine
import time

import psos_util

class PsosService:
    
    def __init__(self, parms):
        self._parms   = parms
        self._name    = self.get_parm("name")
        self.cust     = None
        self.new_cust = None
        
    # get a parameter value
    # return default if parameter not specified
    def get_parm(self,name,default=None):
        return self._parms.get_parm(name,default)
    
    # get a named PSOS service
    def get_svc(self,name):
        return self._parms.get_svc(name)
    
    # return mqtt service
    def get_mqtt(self):
        return self.get_svc("mqtt")

    def lock_lcd(self):
        self.get_svc("lcd").set_lock(True)
        
    def unlock_lcd(self):
        self.get_svc("lcd").set_lock(False)
        
    # methods that define type of device and capabilities
    def is_esp32(self):
        return self.get_parm("sysname") == "esp32"
    def is_rp2(self):
        return self.get_parm("sysname") == "rp2"
    def has_wifi(self):
        return self.get_parm("has_wifi")
        
    
    def get_defaults(self):
        return self._parms._defaults
    
    def get_config(self):
        return self._parms.get_config()
    
    def get_cust(self):
        return self.cust
    def begin_new_cust(self):
        self.new_cust = self.cust.copy()
    def save_new_cust(self):
        if self.new_cust != None:
            self.cust = self.new_cust
            self.save_cust()
            self.new_cust = None
    def discard_new_cust(self):
        self.new_cust = None
        
    
    # Get and save the customization file for this service.
    # Each service has it's own cust file in the /cust/ directory
    def read_cust(self):
        try:
            fn   = self._name+"_cust.json"
            path = self.get_config()["cust"]
            fn   = psos_util.filepath(path,fn)
            if fn == None:
                return None
            
            with open(fn) as f:
                c = ujson.load(f)
                f.close()
                return c
        except:
           return None
           
    def save_cust(self):
        try:
            fn   = self._name+"_cust.json"
            path = self.get_config()["cust"]
            fn   = psos_util.filepath(path,fn)
            
            if fn == None:
                fn = path + "/" + self._name+"_cust.json"
                
            with open(fn,"w") as f:
                ujson.dump(self.cust,f)
                f.close()
                return True
        except OSError:  # open failed
           return False
           
           
    # Reset microcontroller
    # If there is a service named "reset"
    # will use that service.reset() method.
    # Otherwise just use machine.reset()
    def reset(self,rsn=None):
        
        if rsn != None:
            fname = self.get_parm("log_file",None)
            if fname != None:
                f = open(fname,"a")
                f.write(rsn)
                f.write('\n')
                f.close()
            
        svc = self.get_svc("reset")
        if svc != None:
            svc.reset(rsn)
            time.sleep_ms(5000) # in case reset is not immediate
        else:
            print("resetting system: ", rsn)
            time.sleep_ms(5000) # give print time to run before resetting
            machine.reset()
            time.sleep_ms(5000) # in case reset is not immediate


    # if a log service has been defined
    # write a message to the log
    # TODO: add device as prefix to message?
    async def log(self,msg):
        log = self.get_svc("log")
        lcd = self.get_svc("lcd")
         
        if log != None:
            await log.log_msg(self._name,msg)
        else:
            print(self._name + ": " + msg)
    
    # default run method - just return
    async def run(self):
        pass
        


