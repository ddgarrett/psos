
'''
    Customization class
    
    For services that support customization.
    
'''
import uasyncio
import ujson

import psos_util
import gc

class Customization:

    def __init__(self, parms):
        self.parms    = parms
        self.cust     = None
        self.new_cust = None

    def get_cust(self):
        if self.cust == None:
            self.cust = self.read_cust()
            
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
        gc.collect()
        
    
    # Get and save the customization file for this service.
    # Each service has it's own cust file in the /cust/ directory
    def read_cust(self):
        try:
            fn   = self.parms["name"] +"_cust.json"
            path = self.parms["config"]["cust"]
            fn   = psos_util.filepath(path,fn)
            if fn == None:
                return None
            
            with open(fn) as f:
                c = ujson.load(f)
                f.close()
            gc.collect()
            return c
        except:
           return None
           
    def save_cust(self):
        try:
            fn   = self.parms["name"]+"_cust.json"
            path = self.parms["config"]["cust"]
            fn   = psos_util.filepath(path,fn)
            
            if fn == None:
                fn = path + "/" + self.parms["name"]+"_cust.json"
                
            with open(fn,"w") as f:
                ujson.dump(self.cust,f)
                f.close()
            gc.collect()
            return True
        except OSError:  # open failed
           return False
