"""
    MQTT Proxy Server Class
    
    An MQTT Proxy Server that allows MQTT Proxy Clients to connect
    to MQTT via a socket on the Local Area Network.
    
    Clients use the svc_mqtt_proxy_client instead of svc_mqtt
    to connect to this server which then connects to a
    public MQTT server such as HiveMQ.
    
    Intended for private and secure networks only.
    
    Allows a low(er) overhead method of connecting to a public
    MQTT server without encrypting traffic, but not as robust
    or fault toleran as a full MQTT connection.
    
    Clients use simple async sockets to connect to this MQTT Proxy Server
    and then a simple set of commands to send and receive MQTT messages.
    
"""
from psos_svc import PsosService

import uasyncio
import ujson

import network
import queue

import gc

class ModuleService(PsosService):

    def __init__(self, parms):
        super().__init__(parms)
                
        self.host = self.get_parm("host","0.0.0.0")
        self.port = self.get_parm("port",8123)
        self.backlog = self.get_parm("backlog",5)
        self.timeout = self.get_parm("timeout",20)
        
        self.users = {} # dictionary of users to queue

    async def run(self):
        await self.log('Awaiting client connection: {}'.format(network.WLAN(network.STA_IF).ifconfig()[0]))
        self.cid = 0
        # uasyncio.create_task(heartbeat(100))
        self.server = await uasyncio.start_server(self.run_client, self.host, self.port, self.backlog)
        while True:
            await uasyncio.sleep(1000)

    async def run_client(self, sreader, swriter):
        cid = None
        try:
            while True:
                try:
                    rcv = await uasyncio.wait_for(sreader.readline(), self.timeout)
                except uasyncio.TimeoutError:
                    rcv = b''
                if rcv == b'':
                    raise OSError

                cid,res = await self.process_input(cid,rcv)

                # write back response
                swriter.write(res)
                swriter.write('\n')
                await swriter.drain()
        except OSError:
            pass
        
        # Unsubscribe client based on queue for cid
        if cid != None:
            q = self.users[cid]
            await self.get_mqtt().unsubscribe(q)
            del self.users[cid]
        
        await self.log('Client {} disconnect.'.format(cid))
        await sreader.wait_closed()

    async def process_input(self,cid,rcv):
        msg = ujson.loads(rcv.rstrip())
        
        # always require function
        if not "func" in msg:
            return cid, self.set_err("missing func")
        
        # cid = None if client not yet connected
        if cid == None:
             return await self.register_client(cid,msg)
            
        if msg["func"] == "sub":
            return await self.subscribe(cid,msg)
        
        if msg["func"] == "pub":
            return await self.publish(cid,msg)
        
        if msg["func"] == "rcv":
            return await self.check_queue(cid)
        
        return cid, self.set_err("invalid function: {}".format(msg["func"]))
    
    async def subscribe(self,cid,msg):

        if not "topic" in msg:
            return cid, self.set_err("subscribe requires topic")
        
        topic = msg["topic"]
        qos = 0
        if "qos" in msg:
            qos = msg["qos"]
        
        print(cid, "sub", topic)
        
        mqtt = self.get_mqtt()
        q = self.users[cid]
        await mqtt.subscribe(topic,q,qos)
        
        return cid,ujson.dumps({"func":"sub", "topic":topic, "qos":qos})
    
    async def publish(self,cid,msg):
        if not "topic" in msg:
            return cid, self.set_err("publish requires topic")
        
        topic = msg["topic"]
        payload = ""
        qos = 0
        retain = False
        
        if "payload" in msg:
            payload = msg["payload"]
            
        if "qos" in msg:
            qos = msg["qos"]
            
        if "retain" in msg:
            retain = msg["retain"]
            
        print(cid,"pub",topic,payload)
        
        await self.get_mqtt().publish(topic,payload,retain,qos)
        
        return cid,ujson.dumps({"func":"pub", "topic":topic, "payload":payload, "retain":retain, "qos":qos }) 
        
    async def check_queue(self,cid):
        
        q_out = self.users[cid]
        
        if not q_out.empty():
            msg = q_out.get_nowait()
            return cid,ujson.dumps({"func":"rcv", "payload":msg})
            
        return cid,ujson.dumps({"func":"nop"}) 


    async def register_client(self,cid,msg):
        # only accept a connection request
        if msg["func"] != "con":
            return cid, self.set_err("client not connected")
        
        if not "cid" in msg:
            return cid, self.set_err("cid required for connection")
        
        cid = msg["cid"]
        q = queue.Queue()
        
        # IF client is already connected
        # Wait for that socket to timeout
        while cid in self.users:
            await uasyncio.sleep(1)
            
        self.users[cid] = q
            
        await self.log("client connected: {} ".format(cid))
        return cid,ujson.dumps({"func":"con", "payload":cid})        
        
    # return an error response
    def set_err(self,rsn):
       return ujson.dumps({"func":"err", "payload":rsn})

    # never called?
    async def close(self):
        await self.log('Closing server')
        self.server.close()
        await self.server.wait_closed()
        await self.log('Server closed.')
