"""
    Touch Sensor Service Class
    
    Send a sensor touched message when capacitance of
    a specified touch sensor drops below a given value.
    Only send message when sensor goes from not touched
    to touched.
    
    JSON specifies touch sensor threshold and topic to
    send message under.
    
"""

from psos_svc import PsosService
import uasyncio
import queue

from machine import Pin, TouchPad
from svc_lcd_msg import SvcLcdMsg

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        # topic to send LCD hourglass message under
        self._pub_hourglass = parms.get_parm("pub_hourglass",None)
        self._hg_msg = None
        
        if self._pub_hourglass != None:
            self._hg_msg = SvcLcdMsg().dsp_hg().dumps()
        
        # topic to send message under
        self._pub_touch = parms.get_parm("pub_touch")
        
        # touch sensor pin and threshold
        self._t_pin       = parms.get_parm("pin",15)
        self._t_threshold = parms.get_parm("threshold",300)
        
        # init sensor
        self._touch = TouchPad(Pin(self._t_pin))
        
    async def run(self):
        
        mqtt = self.get_mqtt()
        touched = False
        r = 1000
        
        print("starting touch sensor "+self._name)
        
        while True:
            try:
                r = self._touch.read()
            except:
                print("touchpad error")
            
            # sensor being touched?
            if r < self._t_threshold:
                if not touched:
                    await self.pub_hourglass(mqtt)
                    await mqtt.publish(self._pub_touch,r)
                    touched = True
            else:
                touched = False
                    
            await uasyncio.sleep_ms(300)

    async def pub_hourglass(self,mqtt):
        if self._pub_hourglass != None:
            await mqtt.publish(self._pub_hourglass,self._hg_msg)
    
