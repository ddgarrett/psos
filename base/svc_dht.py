"""
    DHT Service Class - Supports DHT11 or DHT22
    
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
        pin = parms.get_parm("dht_pin",4)
        dht22 = parms.get_parm("dht22",False)
        
        if dht22:
            self._sensor = dht.DHT22(Pin(pin))
        else:
            self._sensor = dht.DHT11(Pin(pin))
        
        # when a message is received via the subscribed topic
        # data is written to the trigger_q
        # which then sends updated data in the pub topic
        # self._subscr_topic = parms.get_parm("subscr_upd")
        self._trigger_q = queue.Queue()
        # self._pub_topic = parms.get_parm("pub_upd")
        
    async def run(self):
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self.get_parm("subscr_upd"),self._trigger_q)
        
        while True:
            data = await self._trigger_q.get()
            await self.send_data(mqtt)
            
            
    # send data via MQTT after receiving a update request
    async def send_data(self,mqtt):
        
        # retry 3 times in case of error,
        # waiting 1/2 second between readings
        cnt = 3
        
        while cnt > 0:
            msg = await self.read_data()
            if msg != None:
                await mqtt.publish(self.get_parm("pub_upd"),msg)
                return
                
            cnt = cnt - 1
            await uasyncio.sleep_ms(500)
            
        # no data after 3 tries
        await mqtt.publish(self.get_parm("pub_upd"),{"temp": "starting...", "hum": "...", "dev":self.get_parm("dev")})
            
            
    # read data from DHT device
    async def read_data(self):        
        try:
            self._sensor.measure()
            temp = self._sensor.temperature()
            temp = temp * (9/5) + 32.0
            
            hum = self._sensor.humidity()
    
            temp = ('{0:3.0f}'.format(temp))
            hum =  ('{0:3.0f}'.format(hum))
            
            msg = {"temp": temp, "hum": hum, "dev":self.get_parm("dev")}
                        
            return msg
    
        except OSError as e:
            print("Failed to read sensor")
            return None
