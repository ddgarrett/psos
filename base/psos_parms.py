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
    
    def __init__(self, parms, default_parms, config):
        self._parms = parms
        self._defaults = default_parms
        self.config = config
        
        try:
            self.no_fmt = default_parms["no_format"]
        except KeyError:
            self.no_fmt = ["format"]        
        
    def get_parm(self,key,parm_default=None):
        try:
            r = self._parms[key]
            # if '{' in result
            # and key not in the list of keys to NOT format
            #  - format the result using defaults
            if type(r) == str and '{'in r and not key in self.no_fmt:
                return r.format(**self._defaults)
            return r
        except KeyError:
            pass
        
        try:
            return self._defaults[key]
        except KeyError:
            pass
        
        try:
            return self.config[key]
        except KeyError:
            pass
        
        return parm_default
    
    def set_parm(self,key,value):
        self._parms[key] = value
    
    def get_svc(self,svc_name):
        try:
            return self._defaults["services"][svc_name]
        except KeyError:
            pass
        
        return None
    
    def get_config(self):
        return self.config

    # Supports
    #   a = parms[key]
    # notation. For default values, use:
    #   a = parms[(key,default)]
    # A 2 value tuple with key and default value
    # where default value returned if key not found.
    def __getitem__(self, key):
        if type(key) == tuple and len(key_ == 2):
            # assume I have a default value
            return self.get_parm(key[0],key[1])
        
        return self.get_parm(key)
    
    #  supports:  p[key] = value
    def __setitem__(self, key,value):
        self.set_parm(key,value)
        
    # checks if m is "in" parms
    def __contains__(self, m):
        return self.get_parm(m) != None
