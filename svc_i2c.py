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
        
        # topic to send message under
        # for now, just support I2C(0) with default pins
        self._i2c = I2C(0)  # on esp32 defaults to pins 18 and 19
        
    def get_i2c(self):
        return self._i2c
    
        
            
