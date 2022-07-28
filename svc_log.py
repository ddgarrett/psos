"""
    Log Service Class
    
    Logs messages.
    
"""

from psos_svc import PsosService
import uasyncio

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        self._pub_topic = parms.get_parm("pub_log","log")
        
    async def log_msg(self,name,msg):
        
        mqtt = self.get_svc("mqtt")
        
        log_msg = name + ": " + msg
        
        if mqtt == None:
            print(log_msg)
        else:
            await mqtt.publish(self._pub_topic,log_msg)

        
        

