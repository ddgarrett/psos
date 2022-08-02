"""
    Memory Utilization Service Class
    
    Send memory use messages when prompted.
    
    Messages to topics defined in psos_parms.json for this service
    trigger responses that contain the amount of disk and memory used.
    
"""

from psos_svc import PsosService
import uasyncio
import queue

import os
import gc

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        # when a message is received via the subscribed topic
        # data is written to the trigger_q
        # which then sends updated data in the pub topic
        self._subscr_topic = parms.get_parm("subscr_upd")
        self._trigger_q = queue.Queue()
        self._pub_upd = parms.get_parm("pub_upd")
        
    async def run(self):
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self._subscr_topic,self._trigger_q)
        
        while True:
            data = await self._trigger_q.get()
            await self.send_data(mqtt)
            
            
    # send data via MQTT after receiving a update request
    async def send_data(self,mqtt):
        msg = {
            'disk_free' : self.df(),
            'mem_free'  : self.free() }
        
        await mqtt.publish(self._pub_upd,msg)


    # disk free space
    def df(self):
        s = os.statvfs('//')
        blk_size = s[0]
        total_mb = (s[2] * blk_size) / 1048576
        free_mb  = (s[3] * blk_size) / 1048576
        pct = free_mb/total_mb*100
        return '{0:.2f}MB ({1:.0f}%)'.format(free_mb, pct)
        # return ('DFr {0:.2f}MB {1:.0f}%'.format(free_mb, pct))

    def free(self):
        gc.collect() # run garbage collector before checking memory 
        F = gc.mem_free()
        A = gc.mem_alloc()
        T = F+A
        P = '{0:.0f}%'.format(F/T*100)
        return '{0:,} ({1})'.format(F,P)

