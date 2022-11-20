"""
    GY-521 MPU-6050 Service Class
    
    Uses a the GY-521 3 Axis Accelerometer Gyroscope Module
    to generate menu messages including:
    
    'enter' - tilted to the right
    'up'    - tilted forward
    'down'  - tilted back
    'exit'  - tilted left
    
    
    This in turn triggers the send of a given message to the specified topics.
    Parms:
     - pub = default topic to publish commands values to
     - i2c = I2C service to use for GY-521
     
     Possible future enhancement,
     - allow different topics for each button
     - allow custom message/payload to be sent for each button
     
     For now, there is a single topic and the message sent is as outlined above.
    
"""

from psos_svc import PsosService
import uasyncio
import queue

from svc_lcd_msg import SvcLcdMsg
from imu import MPU6050


# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        # topic to send LCD hourglass message under
        self._pub_hourglass = parms.get_parm("pub_hourglass",None)
        self._hg_msg = None
        
        if self._pub_hourglass != None :
            self._hg_msg = SvcLcdMsg().dsp_hg().dumps()
            
        self.trigger = self.get_parm("trigger",25)
        self.pub = self.get_parm("pub")
        
        i2c_svc = parms.get_parm("i2c")
        i2c = self.get_svc(i2c_svc).get_i2c()
        self.imu = MPU6050(i2c)
        
        
    async def run(self):
        
        mqtt = self.get_mqtt()

        new_state = "--"  # new state
        ns_ticks = 0      # number of times new state detected

        while True:
            ax=int(round(self.imu.accel.x*90))
            ay=int(round(self.imu.accel.y*90))
            
            tr = self.trigger  # trigger angle to detect tilt
            
            # check msg state is stable for 300ms
            # then send a single msg waiting for it to change again
            if ay < -tr:
                msg = "enter"
            elif ay > tr:
                msg = "exit"
            elif ax < -tr:
                msg = "up"
            elif ax > tr:
                msg = "down"
            else:
                msg = "--"

            if msg == new_state:
                ns_ticks += 1
                if ns_ticks == 3:
                    # new state has been triggered for
                    # enough time - send a message
                    
                    if new_state != "--":
                        await self.pub_hourglass(mqtt)
                        await mqtt.publish(self.pub,new_state)
            else:
                new_state = msg
                ns_ticks = 0

                    
            await uasyncio.sleep_ms(100)

    async def pub_hourglass(self,mqtt):
        if self._pub_hourglass != None:
            await mqtt.publish(self._pub_hourglass,self._hg_msg)
    
