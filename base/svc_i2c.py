"""
    I2C Service Class
    
    Set up an I2C Connection which other services can use.
    
"""

from psos_svc import PsosService
from machine import I2C

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        channel = self.get_parm("channel",0)
        
        # topic to send message under
        #  I2C(0)  defaults to scl=18, sda=19
        #  I2C(1)  defaults to scl=25, sda=26
        self._i2c = I2C(channel)  # on esp32 defaults to pins 18 and 19
        
    def get_i2c(self):
        return self._i2c
    
        
            
