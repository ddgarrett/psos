"""
    SD Card Service Class
    
    Mount an SD Card.
    Ensures that only one service takes care of mounting the SD card.
    
"""

#    ESP32-CAM board uses  the SD card to the following pins:
#    SD Card | ESP32    |esp32-cam
#       D2       -          -
#       D3       SS         gpio13
#       CMD      MOSI       gpio15
#       VSS      GND        gnd
#       VDD      3.3V       3.3v
#       CLK      SCK        gpio14
#       VSS      GND        gnd
#       D0       MISO       gpio2
#       D1       -          gpio4 + LED flash also  :(
#   FLASHLED                gpio4
#   red led                 gpio33 (mini smd led below ESP32-controler)
#       SD card socket : pin 9 is SD ( = CARD DETECTION , is a card inserted ?)


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

        slot = self.get_parm("slot",1)
        sck  = self.get_parm("sck",14)
        mosi = self.get_parm("mosi",15)
        miso = self.get_parm("miso",2)
        cs   = self.get_parm("cs",13)
        baud = self.get_parm("baud",1_000_000)
        
        # spi = machine.SPI(1, baudrate=100000, phase=0, polarity=0, sck=machine.Pin(14), mosi=machine.Pin(15), miso=machine.Pin(2)) 
        # sd = sdcard.SDCard(spi, machine.Pin(13))
        
        # spi = machine.SPI(2, baudrate=100000, phase=0, polarity=0, sck=machine.Pin(18), mosi=machine.Pin(23), miso=machine.Pin(19)) 
        # sd = sdcard.SDCard(spi, machine.Pin(5))
        
        spi = machine.SPI(slot, baudrate=baud, phase=0, polarity=0, sck=machine.Pin(sck), mosi=machine.Pin(mosi), miso=machine.Pin(miso)) 
        sd = sdcard.SDCard(spi, machine.Pin(cs))
        
        self._mount_pt = self.get_parm('mount_pt','/sd')
        os.mount(sd,self._mount_pt)
        
    def unmount(self):
        os.umount(self._mount_pt)
        
    async def run(self):
        
        upd = self.get_parm("subscr_upd",None)
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
        
        if len(data) >= 3 and data[2] == "test":
            await self.test_sd()
        
        msg = {
            'disk_free' : self.df(),
            'mem_free'  : self.free() }
        
        await mqtt.publish(self.get_parm("pub_upd"),msg)

    # test SD card read write 
    async def test_sd(self):
        await self.log('******************************')
        await self.log('Root:\t{}'.format(os.listdir()))
        
        os.chdir(self._mount_pt)
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
        s = os.statvfs(self._mount_pt)
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