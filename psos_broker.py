
import queue
import uasyncio
from psos_subtopic import Subtopic


class Broker:
    """
        Publish Subscribe OS (PSOS) Broker Class.
        
        Main class to publish to or subscribe from a topic.

    """
    
    def __init__(self, svc_parms):
        self.root_subtopic = Subtopic("",-1)
        
    def subscribe(self,subscriber):
        topics = subscriber.get_filter().split('/')
        self.root_subtopic.subscribe(topics,subscriber)
        
    def unsubscribe(self,subscriber):
        topics = subscriber.get_filter().split('/')
        self.root_subtopic.unsubscribe(topics,subscriber)
        
        
    # publish a message to a given topic
    #  - topic = string with subtopics separated by '/'
    #  - msg   = a user defined message to be passed to subscribers of the topic
    def publish(self,topic_str,payload):
        topics = topic.split('/')
        self.root_subtopic.publish(topics,payload,topic_str)
