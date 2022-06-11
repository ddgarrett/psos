import queue
import uasyncio

class Subscriber:
    """
        Publish Subscribe OS (PSOS) Subscriber Class.
        
        Subscribe to a topic.
    """
    
    def __init__(self, broker, client, callback, filter):
        self.broker   = broker
        self.client   = client
        self.callback = callback
        self.filter   = filter
        
        broker.subscribe(self)
    
    def get_callback(self):
        return self.callback
    
    def get_filter(self):
        return self.filter
    
    # unsubscribe to the topic
    def unsubscribe(self):
        self.broker.unsubscribe(self)
    
