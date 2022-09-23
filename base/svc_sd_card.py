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



# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)

        # TODO: allow parms to specify details such as pins and mount point name
        spi = machine.SPI(1, baudrate=100000, phase=0, polarity=0, sck=machine.Pin(14), mosi=machine.Pin(15), miso=machine.Pin(2)) 
        sd = sdcard.SDCard(spi, machine.Pin(13))
        
        self._mount_pt = self.get_parm('mount_pt','/sd')
        os.mount(sd,self._mount_pt)
        
    def unmount(self):
        os.umount(self._mount_pt)
        
