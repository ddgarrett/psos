"""
    MQTT Class That Only Logs Publish Requests
    
    Instead of connecting to MQTT writes messages to the specified
    MQTT Log File. This log can then be read after a restart with
    different parms that have an MQTT connected service.
    
    This is done to reduce the memory footprint when it is critical
    to not run out of space even though you are reading large files,
    such as happens when local source is updated via github.
    
"""

from psos_svc import PsosService
import uasyncio
import queue
import gc

from psos_util import to_str,to_bytes
from psos_subscription import Subscription


    
'''
    MQTT Log Published Messages Class
    
'''
# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        self.fn = self.get_parm("log_fn","mqtt_log.txt")
        self.print = self.get_parm("print",True)
            
    async def run(self):       
        pass
    
    # Subscribe to a given topic
    # This version does nothgin so we ignore subscribe requests.
    async def subscribe(self,topic_filter,queue,qos=0):
        pass
    
    # publish messages
    async def publish(self,topic,payload,retain=False, qos=0):
        
        if self.print:
            print(to_str(topic),to_str(payload))
            
        fname = self.fn
        
        if fname != None:
            f = open(fname,"a")
            f.write(self.get_dt())
            f.write('\t')
            f.write(to_bytes(topic))
            f.write('\t')
            f.write(to_bytes(payload))
            f.write('\n')
            f.close()

    # remove all of the subscriptions for a given queue
    async def unsubscribe(self,queue):
        pass
        