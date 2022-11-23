"""
    Command to Calibrate Soil Dry and Wet Readings.
    
"""

from psos_svc import PsosService
import uasyncio

from machine import Pin

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self.menu = self.get_parm("menu")
        svc_soil = self.get_parm("svc_soil")
        self.svc_soil = self.get_svc(svc_soil)

        
    async def run(self):
        self.menu.update_lcd("running test...")
        
        s_raw = 0
        for i in range(5):
            self.menu.update_lcd("running test...\n"+str(i+1))

            values = await self.svc_soil.get_adc_value()
            s_raw += values["raw"]
            
        s_raw /= 5
        s_raw = round(s_raw)
        values["raw"] = s_raw
        values["curr"] = self.svc_soil.dry
        msg = "CURR: {curr}\nNEW: {raw}".format(**values)
        self.menu.update_lcd(msg)
        
