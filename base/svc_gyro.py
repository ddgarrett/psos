"""
    GY-521 MPU-6050 Service Class
    
    Uses a the GY-521 3 Axis Accelerometer Gyroscope Module
    to emulate four "touch buttons", which with the ESP32 are
    placed on the four corners of the circuit board:
    Upper Left (UL), Lower Left (LL),
    Upper Right (UR) and Lower Left (LL).
    
    Buttons are triggered when the gyro is tilted right, left or
    forward, backward:
    UL = right
    LL = left
    UR = forward
    LR = backward
    
    This in turn triggers the send of a given message to the specified topics.
    Parms:
     - pub = default topic to publish button values to
     - i2c = I2C service to use
     
     Possible future enhancement,
     - allow different topics for each button
     - allow custom message/payload to be sent for each button
     
     For now, there is a single topic and the message sent is UL, LL, UR or LR.
    
    
    
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

        state = "--"		# current state
        new_state = "--"	# new state
        ns_ticks = 0		# number of times new state detected

        while True:
            ax=int(round(self.imu.accel.x*90))
            ay=int(round(self.imu.accel.y*90))
            temp=round((self.imu.temperature* 1.8 + 32),1)
            
            button = state
            tr = self.trigger  # trigger angle to detect tilt
            if ay < -tr:
                button = "UL"
            elif ay > tr:
                button = "LL"
            elif ax < -tr:
                button = "UR"
            elif ax > tr:
                button = "LR"
            else:
                button = "--"
                

            if button == new_state:
                ns_ticks += 1
                if ns_ticks == 3:
                    # new state has been triggered for
                    # enough time - send a message
                    state = new_state
                    # new_state = "--"
                    # ns_ticks = 0
                    
                    if state != "--":
                        await self.pub_hourglass(mqtt)
                        await mqtt.publish(self.pub,state)
            else:
                new_state = button
                ns_ticks = 0

                    
            await uasyncio.sleep_ms(100)

    async def pub_hourglass(self,mqtt):
        if self._pub_hourglass != None:
            await mqtt.publish(self._pub_hourglass,self._hg_msg)
    
