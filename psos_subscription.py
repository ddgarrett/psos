'''
    Subscription class defines a subscriber.
    
    Subscriber specifies a filter for subscription
    and a queue to write messages to when received
    from the mqtt broker.
    
    Messages placed in queue are JSON formatted strings
    containing the filter, topic, payload (and perhaps
    additional info to be determined)
'''

import queue
from psos_util import to_str, to_bytes


class Subscription:
    def __init__(self, topic_filter, queue,qos=0):
        self._filter = to_bytes(topic_filter)
        self._filter_split = to_str(topic_filter).split('/')
        self._queue = queue
        self._qos   = qos
        
    def subscribe(self,client):
        print("subscribe "+to_str(self._filter))
        client.subscribe(self._filter,self._qos)
        
    # write the filter, topic and payload to this subscriptions queue
    # if the topic matches matches the filter.
    # topic_split = topic.split('/')
    def put_match(self,topic_split,topic,payload):
        if self.filter_match(topic_split):
            self._queue.put_nowait([to_str(self._filter),to_str(topic),to_str(payload)])
    
    # return True if the topic and queue
    # match this subscription
    def exact_match(self,topic_filter,queue):
        return (self._filter == to_bytes(topic_filter) and
                self._queue  == queue)
    
    # return true if the MQTT filter for this subscription
    # matches the topic
    def filter_match(self,topic_split):
        for i in range(len(self._filter_split)):
            
            # filter matches anything from here on
            if self._filter_split[i] == "#":
                return True
            
            # already reached end of topic_split
            # therefore not a match
            if i >= len(topic_split):
                return False
            
            # matches at this level - continue
            if (self._filter_split[i] == "+" or
                self._filter_split[i] == topic_split[i]):
                continue
            
            # must have a mismatch
            return False
        
        # matches if topic and filter are the same length
        return len(topic_split) == len(self._filter_split)
    
