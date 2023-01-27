"""
    MQTT Class That Only Logs Publish Requests
    
    Instead of connecting to MQTT writes messages to the specified
    MQTT Log File. This log can then be read after a restart with
    different parms that have an MQTT connected service.
    
    This is done to reduce the memory footprint when it is critical
    to not run out of space even though you are reading large files,
    such as happens when local source is updated via github.

    As of Jan 2023, this service can also be used to create an indexed
    log file which can then be read as an indexed array. New methods
    write the index file, return number of entries in main file,
    and allow access to main file via an array of index numbers.

    Indexed log file is create if the "fn_idx" parm specifies a file name.

    Note that care must be taken to keep the two files in sync. NO checking
    is done (yet). Could have re-index option which runs if index file is 
    gone or the last entry in the idx does not point to the end of the log
    file. This would require reading line by line through the main file
    and creating a 4 byte entry in the index file for each line in the log
    file.
    
    When acting in this mode, other services can "subscribe" to this service mqtt_log,
    to receive notification that a new record has been received. This service will then
    forward the message to any subscribers who have subscribed to the topic.
    
    IF this service saves a file to an SD card on a shared SPI bus, specify the
    "spi_lock" parm which should be the name of the SPI service that can be used
    to lock and unlock the SPI while reading and writing to the SD card.
    
"""

from psos_svc import PsosService
import uasyncio
import queue
import gc

from psos_util import to_str,to_bytes,file_sz
from psos_subscription import Subscription
import struct
import os
    
'''
    MQTT Log Published Messages Class
    
'''
# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        self.fn = self.get_parm("log_fn","mqtt_log.txt")
        self.print = self.get_parm("print",True)

        self.fn_idx = self.get_parm("idx_fn",None)

        self.subs = [] # if we are forwarding msg
        
        self.spi_svc = None
        spi_lock = self.get_parm("spi_lock",None)
        if spi_lock != None:
            self.spi_svc = self.get_svc(spi_lock)
            
    # if a subscription topic is specified, we log all of
    # the received info to the log file then forward
    # the info to any other services which have subscribed
    # to the topic.
    async def run(self):
        sub = self.get_parm("sub",None)
        if sub == None:
            return
        
        mqtt = self.get_mqtt()
        
        # Can not be running as the main MQTT service
        # if we are forwarding messages.
        if self == mqtt:
            return
        
        q = queue.Queue()
        await mqtt.subscribe(sub,q)
        while True:
            data = await q.get()
            await self.publish(data[1],data[2])
    
    # Subscribe to a given topic
    # This version does nothgin so we ignore subscribe requests.
    async def subscribe(self,topic_filter,queue,qos=0):
        # logging might cause loop?
        # await self.log("sub mqtt log {}".format(topic_filter))
        
        sub = Subscription(topic_filter,queue,qos)
        self.subs.append(sub)
            
        # give other tasks a chance to run
        await uasyncio.sleep_ms(0)
    
    # publish messages
    async def publish(self,topic,payload,retain=False, qos=0):
        
        if self.print:
            print("svc_mqtt_log publish:",to_str(topic),to_str(payload))
  
        if self.fn != None:
            
            await self.lock_spi()
            
            if self.fn_idx != None:
                self.write_idx()
            
            f = open(self.fn,"a")
            f.write(self.get_dt())
            f.write('\t')
            f.write(to_bytes(topic))
            f.write('\t')
            
            # remove newline - messes log file
            s = to_str(payload).replace("\\n","↵")
            s = s.replace("\n","↵")
            f.write(to_bytes(s))
            
            f.write('\n')
            f.close()
            
            self.unlock_spi()

        # if fowarding msg, send to each matching subscriber
        if len(self.subs) > 0:
            # print("...forwarding {} {}".format(topic,payload))
            await self.local_callback(topic,payload)
            
    # forward messages to local subscribers
    async def local_callback(self,topic,msg):        
        t = to_str(topic)
        m = to_str(msg)
        
        # don't think this would happen,
        # but just in case...
        if t.startswith('local/'):
            t = t[6:]
        
        t_split = t.split('/')
        
        for s in self.subs:
            s.put_match(t_split,t,m)        
            
    # write the current size (next position to write) 
    # as a 4 byte int to the index file
    # IF needed, spi lock should be done before this
    def write_idx(self):
        s = file_sz(self.fn)

        # write 4 bytes to index file
        with open(self.fn_idx,'a') as f:
            f.write(struct.pack("i",s))

    # return number of enties in the main file.
    # this is simply the length of the index file / 4
    async def log_len(self):
        await self.lock_spi()
        s = file_sz(self.fn_idx)
        self.unlock_spi()
        return int(s/4)

    # return the log file entry number idx, where idx is the number
    # of a line in the log file
    async def read_log_entry(self,idx):
        if self.fn_idx == None:
            return None
        
        await self.lock_spi()
        sz = file_sz(self.fn_idx)

        p = idx * 4
        if p > sz:
            self.unlock_spi()
            return None

        p2 = -1
        
        # "rb" = read binary, otherwise error on read
        with open(self.fn_idx,"rb") as f_idx:
            # read this main file position from index file
            f_idx.seek(p)
            p2 = struct.unpack('i', f_idx.read(4))
            
        with open(self.fn) as f:
            f.seek(p2[0])
            ln = f.readline().strip()

        self.unlock_spi()
        return ln

    # remove all of the subscriptions for a given queue
    async def unsubscribe(self,queue):
        pass
    
    async def lock_spi(self):
        if self.spi_svc != None:
            await self.spi_svc.lock()
            
    def unlock_spi(self):
        if self.spi_svc != None:
            self.spi_svc.unlock()
        