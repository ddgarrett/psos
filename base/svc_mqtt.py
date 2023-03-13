"""
    MQTT Class
    
    Class that connects to MQTT and supports
    publish and subscribe.
    
    Other services use this service to publish and subscribe to MQTT. 
    
    Notes:
    1. If topic begins with "local/" this service
       a. removes the "local/" prefix
       b. forwards the message to any services subscribing to the topic
       c. does not forward the message the global MQTT broker
       
    2. If there is no wifi service or the wifi service has not yet connected
       or this service has not yet connected to the MQTT broker,
       it will forward published messages to any subscribed service.
       
       Note that this allows MQTT subscribe/publish to be used without an MQTT broker.
       This can be useful for testing since it allows running the test without
       waiting for WiFi and the MQTT broker. This also allows PSOS to be run on
       microcontrollers without WiFi such as the original Raspberry Pi Pico.
    
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

# make root ca part of this module
from micropython import const
_hivemq_root_ca =  const("""-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY
MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc
h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+
0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U
A5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sW
T8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyH
B5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UC
B5iPNgiV5+I3lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUv
KBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWn
OlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTn
jh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbw
qHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CI
rU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNV
HRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkq
hkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZL
ubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ
3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KK
NFtY2PwByVS5uCbMiogziUwthDyC3+6WVwW6LLv3xLfHTjuCvjHIInNzktHCgKQ5
ORAzI4JMPJ+GslWYHb4phowim57iaztXOoJwTdwJx4nLCgdNbOhdjsnvzqvHu7Ur
TkXWStAmzOVyyghqpZXjFaH3pO3JLF+l+/+sKAIuvtd7u+Nxe5AW0wdeRlN8NwdC
jNPElpzVmbUq4JUagEiuTDkHzsxHpFKVK7q4+63SM1N95R1NbdWhscdCb+ZAJzVc
oyi3B43njTOQ5yOf+1CceWxG1bQVs5ZufpsMljq4Ui0/1lvh+wjChP4kqKOJ2qxq
4RgqsahDYVvTH9w7jXbyLeiNdd8XM2w9U/t7y0Ff/9yi0GE44Za4rF2LN9d11TPA
mRGunUHBcnWEvgJBQl9nJEiU0Zsnvgc/ubhPgXRR4Xq37Z0j4r7g1SgEEzwxA57d
emyPxgcYxn/eR44/KJ4EBs+lVDR3veyJm+kXQ99b21/+jh5Xos1AnX5iItreGCc=
-----END CERTIFICATE-----
""")   
    
'''
    MQTT Class
    
'''
# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)    
        
        self._client = None
        self._subscriptions = []       
        self.wifi    = self.get_svc("wifi")

    def mqtt_callback(self,topic,msg):
        t = to_str(topic)
        m = to_str(msg)
        
        t_split = t.split('/')
        
        for subscr in self._subscriptions:
            subscr.put_match(t_split,t,m)
            
    def exit_svc(self):
        if (self._client != None and
            self.wifi.wifi_connected()):
            self._client.disconnect()
            print("mqtt disconnected")
        
    async def run(self):
                
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
                        # give other tasks a chance to run
                        await uasyncio.sleep_ms(0)
                        
                    self._client.check_msg()
                    gc.collect()
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
                        gc.collect()
                                             
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
                gc.collect()
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
            cert = _hivemq_root_ca          
        
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
            
        # give other tasks a chance to run
        await uasyncio.sleep_ms(0)

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
            if self.get_parm("print_local",False):
                print("pub local: ",topic[6:],payload)
            self.mqtt_callback(to_bytes(topic[6:]),to_bytes(payload))
        else:
            if self._client != None:
                self._client.publish(to_bytes(topic), to_bytes(payload),retain,qos)
                
            # go ahead and publish locally
            else:
                self.mqtt_callback(to_bytes(topic),to_bytes(payload))
                
        # give other tasks a chance to run
        await uasyncio.sleep_ms(0)

    # remove all of the subscriptions for a given queue
    async def unsubscribe(self,queue):
        for s in self._subscriptions:
            if s._queue == queue:
                self._subscriptions.remove(s)
                
  