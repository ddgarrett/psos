import queue
import uasyncio

class Subtopic:
    """
        Publish Subscribe OS (PSOS) Subtopic Class.
        
        Defines a single subtopic level in a topic. Subtopics define one level
        in the topic heirarchy as defined by '/', such as:
            subtopic_1/subtopic_2/subtopic_3
            
        In the above example there would be 3 Subtopic objects, one for
        each subtopic_n.
        
        Maintains a list of subscribers who can be notified by this subtopic
        based on the topic set up in a subscribe.
        
        Also processes new messages, sending the payload to subscribers if
        the filter matches this subtopic.
    """
    
    def __init__(self, subtopic, level):
        self.subtopics   = subtopic
        self.level       = level
        
        # subscribers based on filter ending with '#'
        self.pound_subs  = []
        
        #subscribers based on exact match to filter
        self.subscribers = []
        
        # subtopics that have existing nodes
        self.sub_subtopics = {}
        
    # Add a subscriber based on the subtopics subscribed to.
    # Subtopics is an array of subtopics based on the topic string.
    # This subtopic checks to see if the subtopics array ends with this
    # subtopic, and if so, adds it to it's list of subscribers.
    # If the filter specified by the subtopics does not end with this
    # subtopic, pass it to an object which represents the next subtopic
    # in the subtopics list.
    # Maintains a dicitonary of subtopic objects to subtopic string.
    def subscribe(self,subtopics,subscriber):
        if subtopics[self.level] = '#':
            # NOTE: todo - check if this is the last entry in the subtopics
            # array. If not, error
            self.pound_subs.append(subscriber) 
        else
            next_level = self.level + 1
            if self_next_level >= len(subtopics):
                self.subscribers.append(subscriber)
            else:
                sub_subtopic = self.subtopics[self.next_level]
                if  sub_subtopic in self.sub_subtopics:
                    sub_subtopic_obj = self.sub_subtopics[sub_topic]
                else:
                    sub_subtopic_obj = Subtopic(sub_subtopic,next_level)
                    self.subtopics[sub_subtopic] = sub_subtopic_obj                    
                    
                sub_subtopic_obj.subscribe(subtopics,subscriber)
                
    def unsubscribe(self,subtopics,subscriber):
        if subtopics[self.level] = '#':
            # NOTE: todo - check if this is the last entry in the subtopics
            # array. If not, error
            if subscriber in self.pounds_subs:
                self.pounds_subs.remove(subscriber)
        else
            next_level = self.level + 1
            if self_next_level >= len(subtopics):
                self.subscribers.remove(subscriber)
            else:
                sub_subtopic = self.subtopics[self.next_level]
                if  sub_subtopic in self.sub_subtopics:
                    sub_subtopic_obj = self.sub_subtopics[sub_topic]
                    sub_subtopic_obj.unssubscribe(subtopics,subscriber)


    def publish(self,topics,payload):
        # send message to any subscribers who specified a '#' at this level
        for subscriber in pound_subs:
            subscriber.get_callback(payload,topic_str,subscriber)
            
        next_level = self.level + 1
        # if last subtopic, notify any subscribers
        if len(subtopics) == next_level:
            for subscriber in subscribers:
                subscriber.get_callback(payload,topic_str)
        else:
            next_subtopic_str = topics[next_level]
            if next_subtopic_str in sub_subtopics:
                next_subtopic = sub_subtopics[next_subtopic_str]
                next_subtopic.publish(topics,payload,topic_str)
                

        
