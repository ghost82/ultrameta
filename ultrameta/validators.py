class bounds(object):

    def __init__(self, minimum = None, maximum = None):
        self.minimum = minimum
        self.maximum = maximum
        
    def __call__(self, val):
        if isinstance(val, str):
            val = len(val)
        if self.minimum is not None and val < self.minimum:
            return False
        if self.maximum is not None and val > self.maximum:
            return False
        return True

class value(object):

    def __init__(self, required_value):
        self.required_value = required_value
        
    def __call__(self, val):
        if isinstance(val, str):
            val = len(val)
        return val == self.required_value

