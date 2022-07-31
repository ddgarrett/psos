"""
    I2C Scan Service Class
    
    Send i2c Scan.
    
    Messages to topics defined in psos_parms.json for this service
    trigger responses that contain the results of an I2C Scan.
    
"""

from psos_svc import PsosService
import uasyncio
import queue

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        # when a message is received via the subscribed topic
        # data is written to the trigger_q
        # which then sends updated data in the pub topic
        self._subscr_topic = parms.get_parm("subscr_upd")
        self._trigger_q = queue.Queue()
        self._pub_scan = parms.get_parm("pub_scan")
        
        self._i2c_svc = parms.get_parm("i2c")
        
    async def run(self):
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self._subscr_topic,self._trigger_q)
        
        while True:
            data = await self._trigger_q.get()
            await self.pub_scan(mqtt)
            
    # send scan results via MQTT after receiving a update request
    async def pub_scan(self,mqtt):
        i2c_svc = self.get_svc(self._i2c_svc)
        resp = i2c_svc.get_i2c().scan()
        msg = "I2C addr: {}".format(resp)
        print(msg)
        await mqtt.publish(self._pub_scan,msg)
