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
        self.tr_z    = self.get_parm("tr_z",-90)
        self.pub = self.get_parm("pub",None)
        
        i2c_svc = parms.get_parm("i2c")
        i2c = self.get_svc(i2c_svc).get_i2c()
        self.imu = MPU6050(i2c)
        
        if self.pub != None:
            self.lock = 0
        else:
            # if no publish topic,
            # don't publish messages when device tilted
            self.lock = 1
        
        
    async def run(self):
        
        mqtt = self.get_mqtt()

        new_state = "--"  # new state
        ns_ticks = 0      # number of times new state detected

        while True:
            if self.lock <= 0:
                ax=int(round(self.imu.accel.x*90))
                ay=int(round(self.imu.accel.y*90))
                az=int(round(self.imu.accel.z*90))
                
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

            else:
                # wait at least 1 second if locked
                await uasyncio.sleep_ms(1000)
                    
            await uasyncio.sleep_ms(100)

    # lock or unlock gryo so another service has control over it
    def lock_gyro(self,val):
        if val:
            self.lock += 1
        else:
            self.lock -= 1
        
        
    async def pub_hourglass(self,mqtt):
        if self._pub_hourglass != None:
            await mqtt.publish(self._pub_hourglass,self._hg_msg)
            
    # **** NOT TRUE ***** ==> Poll gyro until there is a change.
    # st = current state (One of returned values below or "--")
    # ticks = number of times to wait for consistent state
    # c = count of readings to average (25ms per reading)
    # ret_flat = return state if flat (default is False)
    #
    # The defaults, ticks=2,st="--",c=5, will return a result
    # with any reading other than flat in a minimum of 225ms,
    # averaging 3 25ms readings which remain consistent 3 times.
    #
    # Returns a state as: 
    # "over" gyro tipped over (upside down)
    # "up" top edge tipped up
    # "down" top edge tipped down
    # "left" gyro tipped left (counter clockwise)
    # "right" gyro tipped right (clockwise)
    # "--"  gyro flat
    #
    async def poll_chg(self,ticks=3,st="--",c=3,ret_flat=False):
        tr = self.trigger
        ns_ticks = 0      # number of times new state detected
        new_state = st
        
        while True:

            r = await self.poll_gyro(3)
            ax = r[0]
            ay = r[1]
            az = r[2]
            
            # check msg state is stable for 300ms
            # then send a single msg waiting for it to change again
            if az < self.tr_z:
                msg = "over"
            elif ay < -tr:
                msg = "right"
            elif ay > tr:
                msg = "left"
            elif ax < -tr:
                msg = "up"
            elif ax > tr:
                msg = "down"
            else:
                msg = "--"

            if msg == new_state:
                ns_ticks += 1
                if ns_ticks >= ticks:
                    # new state has been triggered for
                    # enough time - send a message
                    
                    if ret_flat or new_state != "--":
                        return (r,new_state)
            else:
                new_state = msg
                ns_ticks = 1
                    
            # await uasyncio.sleep_ms(100)

        
    # poll and average a given count (c) of gyro readings
    async def poll_gyro(self,c=5):
        ax = ay = az = gx = gy = gz = tem = 0
        
        # take average of 5 readings
        for i in range(c):
            ax+=self.imu.accel.x
            ay+=self.imu.accel.y
            az+=self.imu.accel.z
            gx+=self.imu.gyro.x
            gy+=self.imu.gyro.y
            gz+=self.imu.gyro.z
            tem+=self.imu.temperature
            await uasyncio.sleep_ms(25)
            
        ax=int(round(ax/c*90))
        ay=int(round(ay/c*90))
        az=int(round(az/c*90))
        gx=round(gx/c)
        gy=round(gy/c)
        gz=round(gz/c)
        tem=round((tem/5* 1.8 + 32))
        
        return (ax,ay,az,gx,gy,gz,tem)
    
