"""
    SD Card Service Class
    
    Mount an SD Card.
    Ensures that only one service takes care of mounting the SD card.
    
    This, version 2, takes the name of an SPI service, svc_spi, instead of
    SPI definitions.
    
"""

from psos_svc import PsosService

import machine
import sdcard
import os
import queue
import gc



# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)

        self.cs_pin   = machine.Pin(self.get_parm("cs",22),machine.Pin.OUT)
        
        spi_svc = parms.get_parm("spi")
        self.spi_svc = self.get_svc(spi_svc)
          
        self.mount_pt = self.get_parm('mount_pt','/sd')
        
    def unmount(self):
        os.umount(self.mount_pt)
        
    async def run(self):
        spi = self.spi_svc.spi
        cs  = self.cs_pin
        baud = self.spi_svc.default["baud"]
        
        await self.spi_svc.lock()
        self.sd = sdcard.SDCard(spi,cs,baudrate=baud)
        os.mount(self.sd,self.mount_pt)
        self.spi_svc.unlock()
        
        gc.collect()
        
        upd = self.get_parm("sub",None)
        if  upd == None:
            return
        
        q = queue.Queue()
        mqtt = self.get_mqtt()
        
        await mqtt.subscribe(upd,q)
        
        while True:
            data = await q.get()
            await self.send_data(mqtt,data)
            
            
    # send data via MQTT after receiving a update request
    async def send_data(self,mqtt,data):
        
        await self.spi_svc.lock()

        if len(data) >= 3 and data[2] == "test":
            await self.test_sd()
        
        msg = {
            'disk_free' : self.df(),
            'mem_free'  : self.free() }
        
        self.spi_svc.unlock()
        await mqtt.publish(self.get_parm("pub"),msg)

    # test SD card read write 
    async def test_sd(self):
        await self.log('******************************')
        await self.log('Root:\t{}'.format(os.listdir()))
        
        os.chdir(self.mount_pt)
        await self.log('SD Card:\t{}'.format(os.listdir()))
        
        await self.log('Write to SD Card')
        f = open('sample2.txt', 'w')
        f.write('Some text for sample 2\n')
        f.close()
        
        await self.log('Read from SD Card')
        f = open('sample2.txt')
        await self.log(f.read())
        f.close()
         
        await self.log('Append to file')
        f = open('sample2.txt', 'a')
        f.write('More text for sample 2\n')
        f.close()
        
        await self.log('Read from SD Card')
        f = open('sample2.txt')
        await self.log(f.read())
        f.close()

        await self.log('Delete Sample File')
        os.remove('sample2.txt')

        await self.log("test complete")
        os.chdir('/')
        await self.log('******************************')
        
    # disk free space
    def df(self):
        s = os.statvfs(self.mount_pt)
        blk_size = s[0]
        total_mb = (s[2] * blk_size) / 1048576
        free_mb  = (s[3] * blk_size) / 1048576
        pct = free_mb/total_mb*100
        return '{0:,.2f}MB ({1:.0f}%)'.format(free_mb, pct)
        # return ('DFr {0:.2f}MB {1:.0f}%'.format(free_mb, pct))

    def free(self):
        gc.collect() # run garbage collector before checking memory 
        F = gc.mem_free()
        A = gc.mem_alloc()
        T = F+A
        P = '{0:.0f}%'.format(F/T*100)
        return '{0:,} ({1})'.format(F,P)