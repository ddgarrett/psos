"""
    PSOS Service Class
    
    Superclass of all PSOS Services
    
"""

import uasyncio
import ujson

import machine
import time

import psos_util
import gc

class PsosService:
    
    def __init__(self, parms):
        self._parms   = parms
        self._name    = self.get_parm("name")
        self.svc_lcd  = None
        
        '''  moved to psos_cust Customization class
        self.cust     = None
        self.new_cust = None
        '''
        
        self.tz       = self.get_parm("tz",-8)
        self.dev      = self.get_parm("dev","?")
        
        self.lcd_pl   = ("clear",{"msg":None})
        
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

    def get_svc_lcd(self):
        if self.svc_lcd == None:
            lcd = self.get_parm("lcd","lcd")
            self.svc_lcd = self.get_svc(lcd)
            
        return self.svc_lcd
            
    def lock_lcd(self):
        self.get_svc_lcd().set_lock(True)
    def unlock_lcd(self):
        self.get_svc_lcd().set_lock(False)
        
    # complete payload such as:  ["clear",{"msg":"some message"}]
    def display_lcd_payload(self,payload):
        lcd = self.get_svc_lcd()
            
        if lcd != None:
            lcd.write_direct(payload)
            
    # just a text message that clears the screen
    # before the message is displayed.
    # example: self.display_lcd_msg("some message")
    # becomes: self.display_lcd_payload(["clear",{"msg":"some message"}])
    def display_lcd_msg(self,msg):
        # self.display_lcd_payload(["clear",{"msg":msg}])
        self.lcd_pl[1]["msg"] = msg
        self.display_lcd_payload(self.lcd_pl)
        gc.collect()
        
    # methods that define type of device and capabilities
    def is_esp32(self):
        return self.get_parm("sysname") == "esp32"
    def is_rp2(self):
        return self.get_parm("sysname") == "rp2"
    def has_wifi(self):
        return self.get_parm("has_wifi")
        
    # get formatted date and time
    def get_dt(self):
        t = time.localtime(time.mktime(time.localtime())+self.tz*3600)
        return "{1}/{2}/{0}\t{3}:{4:02d}:{5:02d}".format(*t)
    
    def get_defaults(self):
        return self._parms._defaults
    
    def get_config(self):
        return self._parms.get_config()
               
           
    # Reset microcontroller
    # If there is a service named "reset"
    # will use that service.reset() method.
    # Otherwise just use machine.reset()
    def reset(self,rsn=None):
        
        if rsn != None:
            self.display_lcd_msg(str(rsn))
            
            fname = self.get_parm("log_file",None)
            if fname != None:
                f = open(fname,"a")
                f.write(self.get_dt())
                f.write('\t')
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
    async def log(self,msg):
        log = self.get_svc("log")
         
        if log != None:
            await log.log_msg(self._name,msg)
        else:
            print(self._name,":",str(msg))
    
    # default run method - just return
    async def run(self):
        pass
        


