"""
    DHT11 Service Class
    
    Send temperature and humidity messages when prompted.
    
    Messages to topics defined in psos_parms.json for this service
    trigger responses that contain the temperature or humidity readings
    for the attached dht11 sensor.
    
"""

from psos_svc import PsosService
import uasyncio
from machine import Pin
import dht
import queue

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        pin = parms.get_parm("dht11_pin",4)
        self._sensor = dht.DHT11(Pin(pin))
        
        # when a message is received via the subscribed topic
        # data is written to the trigger_q
        # which then sends updated data in the pub topic
        self._subscr_topic = parms.get_parm("subscr_upd")
        self._trigger_q = queue.Queue()
        self._pub_topic = parms.get_parm("pub_upd")
        
    async def run(self):
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self._subscr_topic,self._trigger_q)
        
        while True:
            data = await self._trigger_q.get()
            await self.send_data()
            
            
    # send data via MQTT after receiving a update request
    async def send_data(self):
        

        try:
            self._sensor.measure()
            temp = self._sensor.temperature()
            temp = temp * (9/5) + 32.0
            
            hum = self._sensor.humidity()
    
            temp = ('{0:3.1f}'.format(temp))
            hum =  ('{0:3.1f}'.format(hum))
            
            # msg = "Office temp: {0:3.1f}, humidity: {1:3.1f}".format(temp,hum)

            msg = {"temp": temp, "hum": hum}
            
            # print("temp: "+str(temp)+", humidity:" + str(hum))
            # await self.log(msg)
            
            mqtt = self.get_mqtt()
            # await self.log("updating temp and humidity")
            await mqtt.publish(self._pub_topic,msg)
            # break # exit loop
    
        except OSError as e:
            print("Failed to read sensor")
            mqtt = self.get_mqtt()
            await mqtt.publish(self._pub_topic,{"temp": "starting...", "hum": "..."})

