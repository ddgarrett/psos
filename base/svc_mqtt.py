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
from psos_util import to_str, to_bytes
import sys
import time
import gc
import utf8_char


# not present on non-wifi pico
try:
    from umqtt_simple import MQTTClient
except ImportError:
    pass

from psos_subscription import Subscription


    
'''
    MQTT Class
    
'''
# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)    
        
        self._client = None
        self._subscriptions = []       
            
    def mqtt_callback(self,topic,msg):
        t = to_str(topic)
        m = to_str(msg)
        
        t_split = t.split('/')
        
        for subscr in self._subscriptions:
            subscr.put_match(t_split,t,m)
            
    async def run(self):
                
        self.wifi = self.get_svc("wifi") 
        ping_wait = 0
        
        # NOTE: below populates self.svc_lcd
        self.get_svc_lcd()
        if self.svc_lcd != None:
            self.svc_lcd.set_sym(utf8_char.SYM_EX_OUT)
        
        while True:
            if (self._client != None and
                self.wifi.wifi_connected()):
                
                try:
                    ping_wait = ping_wait + 1
                    if ping_wait > 150:
                        ping_wait = 0
                        self._client.ping()
                        # print("pinged mqtt")
                        
                    self._client.check_msg()
                except Exception as e:
                    print("MQTT error: ",e)
                    self._client = None
                    
            else:
                self._client = None
                    
                # not connected
                # try connecting if we have wifi
                if self.wifi != None and self.wifi.wifi_connected():
                    self.display_lcd_msg("MQTT connect...") 
                        
                    print("connecting to MQTT")
                    await self._retry_connect_mqtt()
                        
                    if self._client != None:
                        if self.svc_lcd != None:
                            self.svc_lcd.set_sym(utf8_char.SYM_WIFI)
                            self.display_lcd_msg("MQTT connected")
                            
                        await self.resubscribe()
                                             
            await uasyncio.sleep_ms(100)
            
    async def _retry_connect_mqtt(self,try_cnt=1):
        err = ""
        while try_cnt > 0:
            try:
                # try to reduce ENOMEM on reconnects
                self._client = None
                gc.collect()

                self._client = self._connect_mqtt()
                print("connected to mqtt")
                break
            except Exception as e:
              err = str(e)
              print("error connecting to MQTT: " + err)
              try_cnt = try_cnt - 1

               
            await uasyncio.sleep_ms(300)
            

        if try_cnt <= 0:
            self.reset("unable to connect to MQTT: "+ err)

        
        
    def _connect_mqtt(self):
        
        broker = self.get_parm("broker")
        print("connecting to MQTT broker "+broker)
        
        mqtt_secrets = secrets.mqtt[broker]
        server = mqtt_secrets['server']
        port   = mqtt_secrets['port']
        
        username = None
        password = None
        cert     = None
        
        client = None
        
        cid = ubinascii.hexlify(machine.unique_id())
        
        if 'username' in mqtt_secrets:
            username = mqtt_secrets['username']
            password = mqtt_secrets['password']
        
        if 'ca_cert' in mqtt_secrets:
            cert = mqtt_secrets['ca_cert']          
        
        ssl_params = {}
        if cert != None:
            ssl_params = {"server_hostname":server, "cert":cert}
            
        if username != None:
            
            if cert != None:
                client = MQTTClient(cid, server,
                                          user=username, password=password, port=port,
                                          keepalive=30, ssl=True, ssl_params=ssl_params)
            else:
                client = MQTTClient(cid, server,
                                          user=username, password=password, port=port,
                                          keepalive=30)
        else:
            client = MQTTClient(cid, server, port=port, keepalive=30)
            
        client.set_callback(self.mqtt_callback)
        client.connect()
        
        return client
    
    
    # Subscribe to a given topic
    # Payloads received for the topic are placed on queue.
    # Tasks can therefore just go into a wait
    # until a payload to be written to a queue.
    async def subscribe(self,topic_filter,queue,qos=0):
        await self.log("subscr " + topic_filter)
        
        sub = Subscription(topic_filter,queue,qos)
        self._subscriptions.append(sub)
        if self._client != None:
            sub.subscribe(self._client)

    # when first connected or after reconnect
    # resubscribe to all previous subscriptions
    async def resubscribe(self):
        for sub in self._subscriptions:
            await self.log("resubscr " + to_str(sub._filter))
            sub.subscribe(self._client)
    
    # publish messages
    async def publish(self,topic,payload,retain=False, qos=0):
        # if local topic, only send to local services
        if topic.startswith('local/'):
            self.mqtt_callback(to_bytes(topic[6:]),to_bytes(payload))
        else:
            if self._client != None:
                self._client.publish(to_bytes(topic), to_bytes(payload),retain,qos)
                
            # go ahead and publish locally
            else:
                self.mqtt_callback(to_bytes(topic),to_bytes(payload))

    # remove all of the subscriptions for a given queue
    async def unsubscribe(self,queue):
        for s in self._subscriptions:
            if s._queue == queue:
                self._subscriptions.remove(s)
        