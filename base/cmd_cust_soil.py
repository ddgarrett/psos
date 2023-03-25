"""
    Command to Customize Soil Dry and Wet Readings.
    
"""

from psos_svc import PsosService
import uasyncio

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self.menu = self.get_parm("menu")
        svc_soil = self.get_parm("svc")
        self.svc = self.get_svc(svc_soil)
        self.attr = self.get_parm("attr")
        
        self.svc.cust.begin_new_cust()
        
    async def run(self):
        self.menu.update_lcd("running test...")
        
        s_raw = 0
        for i in range(5):
            self.menu.update_lcd("running test...\n"+str(i+1))

            values = await self.svc.get_adc_value()
            s_raw += values["raw"]
            
        s_raw /= 5
        s_raw = round(s_raw)
        
        self.svc.cust.new_cust[self.attr] = s_raw
        
        v = {}
        v["raw"] = s_raw
        v["curr"] = self.svc.cust.cust[self.attr]
        msg = "CURR: {curr}\nNEW: {raw}".format(**v)
        self.menu.update_lcd(msg)
        
        
