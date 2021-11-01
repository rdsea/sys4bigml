class Metric(object):
    """
    This class defines the common attribute and provide basic function for handling a metric
    - Attribute: 
        - name: name of the metric
        - description: describe the metric
        - value: value of the metric
        - others: (Developing)

    - Function: 
        - set: set specific value
        - get_val: return current value
        - get_name: return metric name
        - get_des: return metric description
        - other: (Developing)
    """
    def __init__(self, metric_name, description, default_value=-1):
        self.metric_name = metric_name
        self.description = description
        self.value = default_value
    
    def set(self, value):
        self.value = value
    def get_val(self):
        return self.value
    def get_name(self):
        return self.metric_name
    def get_des(self):
        return self.description
    def __str__(self) -> str:
        return "metric_name:" + self.metric_name + ", " + "value:" + str(self.value)
    def to_dict(self):
        mectric_dict = {}
        mectric_dict[self.metric_name] = self.value
        return mectric_dict

class Counter(Metric):
    """
    This class inherit all attributes of Metric
    - Attribute: (Developing)

    - Function: 
        - inc: increase its value by num
        - reset: set the value back to zero
        - others: (Developing)
    """
    def inc(self,num=1):
        self.value += num
    
    def reset(self):
        self.value = 0

class Gauge(Metric):
    """
    This class inherit all attributes of Metric
    - Attribute: (Developing)

    - Function: 
        - inc: increase its value by num
        - others: (Developing)
    """
    def inc(self,num):
        self.value += num
    # TO DO:
    # implement other functions
    def dec(self,num):
        self.value -= num
    def set(self,val):
        self.value = val

class Summary(Metric):
    """
    This class inherit all attributes of Metric
    - Attribute: (Developing)

    - Function: 
        - inc: increase its value by num
        - others: (Developing)
    """
    def inc(self,num):
        self.value += num
    # TO DO:
    # implement other functions
    def dec(self,num):
        self.value -= num
    def set(self,val):
        self.value = val

class Histogram(Metric):
    """
    This class inherit all attributes of Metric
    - Attribute: (Developing)

    - Function: 
        - inc: increase its value by num
        - others: (Developing)
    """
    def inc(self,num):
        self.value += num
    # TO DO:
    # implement other functions
    def dec(self,num):
        self.value -= num
    def set(self,val):
        self.value = val

