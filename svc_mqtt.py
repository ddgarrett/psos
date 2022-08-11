"""
    MQTT Class
    
    Class that connects to MQTT and supports
    publish and subscribe.
    
"""

from psos_svc import PsosService
import uasyncio
import ubinascii
import machine
import secrets
import queue
from umqtt.simple import MQTTClient
from psos_util import to_str, to_bytes
import sys
import time
import gc

from psos_subscription import Subscription


    
'''
    MQTT Class
    
'''
# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self._client_id = ubinascii.hexlify(machine.unique_id())
        self._client = None
        self._subscriptions = []
        
        print("mqtt: free space "+str(gc.mem_free()))
        self._retry_connect_mqtt()
        
        gc.collect()
        print("mqtt: free space "+str(gc.mem_free()))
        
        if self._client == None:
            print("unable to connect to MQTT")
            sys.exit(1)
            
        
        
    def mqtt_callback(self,topic,msg):
        t = to_str(topic)
        m = to_str(msg)
        
        t_split = t.split('/')
        
        for subscr in self._subscriptions:
            subscr.put_match(t_split,t,m)
            
        
    async def run(self):

        ping_wait = 0
        
        while True:
            
            # check for any subscribed messages
            # ping MQTT every 200 loops
            if self._client != None:
                try:
                    ping_wait = ping_wait + 1
                    if ping_wait > 200:
                        ping_wait = 0
                        self._client.ping()
                        # print("pinged mqtt")
                        
                    self._client.check_msg()
                except OSError as e:
                    print(e)
                    self._client.disconnect()
                    self._client = None 
                    
            await uasyncio.sleep_ms(100)
            
    def _retry_connect_mqtt(self,try_cnt=3):
        while try_cnt > 0:
            try:
              self._client = self._connect_mqtt()
              print("connected to mqtt")
              break
            except OSError as e:
              print("error connecting to MQTT: " + str(e))
              try_cnt = try_cnt - 1
              
            time.sleep_ms(500)
        
        
    def _connect_mqtt(self):
        wifi = self.get_svc("wifi")
        
        broker = self.get_parm("broker")
        print("connecting to MQTT broker "+broker)
        
        mqtt_secrets = secrets.mqtt[broker]
        mqtt_server = mqtt_secrets['server']
        mqtt_port   = mqtt_secrets['port']
        
        mqtt_username = None
        mqtt_password = None
        cert_data     = None
        
        client = None
        
        if 'username' in mqtt_secrets:
            mqtt_username = mqtt_secrets['username']
            mqtt_password = mqtt_secrets['password']
        
        if 'ca_cert' in mqtt_secrets:
            cert_data = mqtt_secrets['ca_cert']
            
        
        ssl_params = {}
        if cert_data != None:
            ssl_params = {"server_hostname":mqtt_server, "cert":cert_data}
            
        if mqtt_username != None:
            
            if cert_data != None:
                client = MQTTClient(self._client_id, mqtt_server,
                                          user=mqtt_username, password=mqtt_password, port=mqtt_port,
                                          keepalive=30, ssl=True, ssl_params=ssl_params)
            else:
                client = MQTTClient(self._client_id, mqtt_server,
                                          user=mqtt_username, password=mqtt_password, port=mqtt_port,
                                          keepalive=30)
        else:
            client = MQTTClient(self._client_id, mqtt_server, port=mqtt_port, keepalive=30)
            
        client.set_callback(self.mqtt_callback)
        client.connect()
        
        print("mqtt: free space "+str(gc.mem_free()))
        # try to free up some memory
        # ssl_params = {}
        # cert_data = None
        # gc.collect()
        # print("mqtt: free space "+str(gc.mem_free()))
        
        return client
    
    
    # Subscribe to a given topic
    # Payloads received for the topic are placed on queue.
    # Tasks can therefore just go into a wait
    # until a payload to be written to a queue.
    async def subscribe(self,topic_filter,queue,qos=0):
        await self.log("subscribing to " + topic_filter)
        
        sub = Subscription(topic_filter,queue,qos)
        self._subscriptions.append(sub)
        sub.subscribe(self._client)
    
    # publish messages
    async def publish(self,topic,payload,retain=False, qos=0):
        self._client.publish(to_bytes(topic), to_bytes(payload),retain,qos)
        

        
        
                
        
        


