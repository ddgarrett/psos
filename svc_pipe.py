"""
    Pipe Service Class
    
    Transfer a message from an subscribed topic to a publish topic.
    
    Message may be reformatted using a python formatted string
    and JSON input object.
    
    Publish may be to a different MQTT broker (not yet implemented).
    
"""

from psos_svc import PsosService
import uasyncio
import queue

from svc_msg import SvcMsg


# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self._subscr_topic = parms.get_parm("subscr_in")
        self._trigger_q = queue.Queue()
        self._pub_topic = parms.get_parm("pub_out")
        self._format    = parms.get_parm("format","").replace("'",'"')

        
    async def run(self):
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self._subscr_topic,self._trigger_q)
        msg = SvcMsg()
        
        while True:
            data = await self._trigger_q.get()
            msg.load_subscr(data)
            await self.send_data(mqtt,msg)
            
            
    # send data via MQTT after receiving an input message
    async def send_data(self,mqtt,msg):

        out = msg.get_payload()
        
        if self._format != "":
            out_t = self._format.format(**out)
            

        await mqtt.publish(self._pub_topic,out_t)
