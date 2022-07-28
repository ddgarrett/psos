"""
    PSOS Parms Class
    
    Parms for a single object.
    Wraps a dictionary of parms for an object.
    
    A default parms dictionary is also incorporated.
    Values in the default parms will be available to all instances of this class.
    Defaults can be set as well as read, but setting should generally be done
    only by the startup which reads defaults from a .json file
    and runs initialization modules to define addtional defaults.
    
    A dictionary of services is also in the default dictionary.
    The values in that dictionary can be accessed via the get_svc(name) method.
    
    Calls to get_parm specify a name and a default value.
    If name is not in the instance specific dictionary,
    get_parm will check the default dictionary
    If name is not in the default dictionary
    get_parm will return the default value.

"""

class PsosParms:
    
    def __init__(self, parms, default_parms):
        self._parms = parms
        
        # make sure default parms include a services dictionary
        if not "services" in default_parms:
            default_parms["services"] = {}
            
        self._defaults = default_parms
        

    def get_parm(self,parm_name, parm_default=None):
        if parm_name in self._parms:
            return self._parms[parm_name]
        
        if parm_name in self._defaults:
            return self._defaults[parm_name]
        
        return parm_default
        
    def get_svc(self,svc_name):
        if svc_name in self._defaults["services"]:
            return self._defaults["services"][svc_name]
        
        return None


        
