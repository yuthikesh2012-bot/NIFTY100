import time
class RateLimiter:
    def __init__(self,delay:float=1.0): self.delay=delay
    def wait(self): time.sleep(self.delay)
