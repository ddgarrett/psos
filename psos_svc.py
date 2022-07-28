"""
    PSOS Service Class
    
    Superclass of all PSOS Services
    
"""

import uasyncio
import queue

class PsosService:
    
    def __init__(self, parms):
        self._parms  = parms
        self._name   = self.get_parm("name")
        
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

    # if a log service has been defined
    # write a message to the log
    # TODO: add device as prefix to message?
    async def log(self,msg):
        log = self.get_svc("log")
         
        if log != None:
            await log.log_msg(self._name,msg)
        else:
            print(self._name + ": " + msg)
    
    # default run method - just return
    async def run(self):
        pass
        


