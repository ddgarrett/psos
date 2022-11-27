"""
    Command to Save Service Customizations.
    
"""

from psos_svc import PsosService

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        menu = self.get_parm("menu")
        svc = self.get_parm("svc")
        svc = self.get_svc(svc)
        
        if self.get_parm("save",False):
            if svc.new_cust == None:
                menu.update_lcd("NO CHANGES MADE")
            else:
                svc.save_new_cust()
                menu.update_lcd("Change Saved")
        else:
            if svc.new_cust == None:
                menu.update_lcd("Exited")
            else:
                svc.discard_new_cust()
                menu.update_lcd("Change Discarded")
        
              
