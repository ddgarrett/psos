"""
    General Service Message class.
    
    Aids building a message that is sent via MQTT to a service.

"""

import ujson

class SvcMsg:
    
    def __init__(self,f="",t="",payload=""):
        self._filter  = f
        self._topic   = t
        self._payload = payload
        
    # load object passed from a PSOS Subscription
    # It should contain a filter, topic, and payload.
    # Payload may be a JSON string. Assume it is IF
    # it starts with a '{' or '['
    def load_subscr(self,q):
        self._filter = q[0]
        self._topic  = q[1]
        self._payload = q[2]
        
        if (self._payload.startswith('[') or
            self._payload.startswith('{')):
            self._payload = ujson.loads(self._payload)
                
    def set_payload(self,payload):
        self._payload = payload
        return self
    
    def get_payload(self):
        return self._payload
    
    # dumps will generate a string version of this object
    def dumps(self):
        msg = [self._filter, self._topic, self._payload]
        return ujson.dumps(msg)
        
    # load a json string message
    def loads(self,s):
        msg = ujson.loads(s)
        self._filter  = msg[0]
        self._topic   = msg[1]
        self._payload = msg[2]
        
        return self

    

        
    
