"""
    Data Logger Service Class
    
    Log all messages sent to specified topics.
    Messages are written to the SD card.
    
"""

from psos_svc import PsosService
import uasyncio
import queue

import os
import time
import ujson

from svc_msg import SvcMsg

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        # when a message is received via the subscribed topic
        # data is written to the trigger_q
        # which then sends updated data in the pub topic
        self._trigger_q = queue.Queue()
    
        self._file_name = self.get_parm("file_name","data.txt")
        self._format = self.get_parm("format","{dt}\t{topic}\t{payload}")
        
        
    async def run(self):
        
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self.get_parm("subscr_log","#"),self._trigger_q)
        
        # make sure log file already exists
        open(self._file_name,"a").close()
        
        # log current file size
        s = os.stat(self._file_name)
        await self.log("file {0} ({1:.1f}k)".format(self._file_name,s[6]/1024))
        
        while True:
            data = await self._trigger_q.get()
            await self.log_data(data)
            
    # write to disk a time stamp followed by topic and payload
    async def log_data(self,data):
        
        out = {"topic":data[1]}
        data[2] = data[2].replace('\n','↩')
        
        if data[2].startswith('{'):
            out.update(ujson.loads(data[2]))
            
        out['payload'] = data[2]
            
        # get time adjusted to local timezone
        # format time as mm/dd/yyyy hh:mm:ss
        t = time.localtime(time.mktime(time.localtime()) - 7*3600)
        out['dt'] = "{1}/{2}/{0}\t{3}:{4:02d}:{5:02d}".format(*t)
        
        # open data file for appending
        f = open(self._file_name,"a")
        f.write(self._format.format(**out))
        f.write('\n')
        f.close()
        