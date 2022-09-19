"""
    MQTT Proxy Client Class
    
    Connects to MQTT via an MQTT Proxy Server
    on the Local Area Network.
    
    Used instead of svc_mqtt to connect to a public
    MQTT server such as HiveMQ.
    
    Intended for private and secure networks only.
    
    Allows a low(er) overhead method of connecting to a public
    MQTT server without encrypting traffic, but not as robust
    or fault toleran as a full MQTT connection.
    
    Uses simple async sockets to connect to an MQTT Proxy Server
    and then a simple set of commands to send and receive
    MQTT messages.
    
"""

from psos_svc import PsosService
import uasyncio
import usocket

import ubinascii
import machine
import queue
from psos_util import to_str, to_bytes
import sys
import time
import gc
import os
import ujson
import queue

from psos_subscription import Subscription

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self._server = self.get_parm("server")
        self._port   = self.get_parm("port")
        
        self._sock = None
        self._subscriptions = []
        
        self._connected = False

        self._q_send = queue.Queue()
        
        gc.collect()
        
            
    async def run(self):
            
        await self.retry_connect_mqtt_proxy()
        
        if self._sock == None:
            print("unable to connect to MQTT proxy server... exiting")
            sys.exit()

        print("mem: ",self.free())
        
        while True:
            # check for any subscribed messages
            try:
                # send any queued pub/sub messages
                while not self._q_send.empty():
                    await self.send_msg(self._q_send.get_nowait())
                    
                # see if any incoming MQTT messages
                await self.check_msg()
                    
            except Exception as e:
                self.close_sock()
                self.reset("MQTT Proxy Client :"+str(e))
                    
            await uasyncio.sleep_ms(100)
            
    async def retry_connect_mqtt_proxy(self,try_cnt=3):

        while try_cnt > 0:
            try:
                await self.connect_mqtt_proxy()
                if self._sock != None:
                    print("connected to mqtt proxy {}:{}".format(self._server, self._port))
                    self._connected = True
                break
            except OSError as e:
                print('Error connecting to {} on port {}'.format(self._server, self._port))
                self.close_sock()
                try_cnt = try_cnt - 1
               
            # NOTE: NOT an async sleep
            # Want to wait until connection made
            time.sleep_ms(2000)
            
        if try_cnt <= 0:
            print('Unable to {} on port {}'.format(self._server, self._port))
            sys.exit()
        
        
    async def connect_mqtt_proxy(self):

        print("connecting to MQTT Proxy Server")
        self._sock = usocket.socket()
        serv = usocket.getaddrinfo(self._server, self._port)[0][-1]
        self._sock.connect(serv)
        
        self.sreader = uasyncio.StreamReader(self._sock)
        self.swriter = uasyncio.StreamWriter(self._sock, {})
        
        print("connected to proxy server")
        
        cid = ubinascii.hexlify(machine.unique_id())
        broker = self.get_parm("broker")

        resp = await self.send_msg({"func":"con","cid":cid, "mqtt":broker})
        
        if "func" in resp and "payload" in resp:
            if resp["func"] != "con" or resp["payload"] != cid.decode("utf-8"):
                print("unexpected connection response: ", resp)
                self.close_sock()
        else:
            print("unexpected connection response: ", resp)
            self.close_sock()

        
    # Subscribe to a given topic
    # Payloads received for the topic are placed on queue.
    # Subscribed tasks can therefore just go into a wait
    # until a payload to be written to a queue.
    async def subscribe(self,topic_filter,queue,qos=0):
        
        await self.log("sub: " + topic_filter)
        
        sub = Subscription(topic_filter,queue,qos)
        self._subscriptions.append(sub)
        
        msg = {"func":"sub","topic":topic_filter, "qos":qos}
        resp = await self.q_msg(msg)
    
    # publish messages
    async def publish(self,topic,payload,retain=False, qos=0):
        msg = {"func":"pub", "topic":topic, "payload":payload, "retain":retain, "qos":qos}     
        print("pub: ",msg["payload"])
        resp = await self.q_msg(msg)

    # check for any messages
    # If found, pass to callback
    async def check_msg(self):
        func = "rcv"
        
        while func == "rcv":
            msg = {"func":"rcv"}
            resp = await self.send_msg(msg)
            func = resp["func"]
            if func == "rcv":
                await self.mqtt_callback(resp["topic"],resp["payload"])
            else:
                # TODO: check responses?
                pass
    
    async def mqtt_callback(self,topic,msg):
        t = to_str(topic)
        m = to_str(msg)
        
        t_split = t.split('/')
        
        for subscr in self._subscriptions:
            subscr.put_match(t_split,t,m)
            
    async def q_msg(self,msg):
        self._q_send.put_nowait(msg)
        
    # send a message to the mqtt proxy server
    # and receive a response
    async def send_msg(self,msg):
        try:
            # print("sending msg: ",msg)
            self.swriter.write('{}\n'.format(ujson.dumps(msg)))
            await self.swriter.drain()
            resp = await self.sreader.readline()
            return ujson.loads(resp)
        except OSError as e:
            self.close_sock()
            print('Server disconnect.')
            return {"err":e}
        except ValueError as e:
            print("received invalid json response: ",resp)
            self.close_sock()
            return {"err":e}

    def close_sock(self):
        if self._sock != None:
            self._sock.close()
            self._sock = None
        self._connected = False
        
        # while debugging only!!!
        # sys.exit()
    
    def free(self):
        gc.collect() # run garbage collector before checking memory 
        F = gc.mem_free()
        A = gc.mem_alloc()
        T = F+A
        P = '{0:.0f}%'.format(F/T*100)
        return '{0:,} ({1})'.format(F,P)