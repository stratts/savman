from datetime import datetime

class Timer:
    def __init__(self):
        self.started = None
        self.finished = None
        self.elapsed = None
        self.seconds = None

    def start(self):
        self.started = datetime.now()

    def stop(self):
        self.finished = datetime.now()
        self.elapsed = self.finished-self.started
        sectime = ((self.elapsed.seconds*1000000)+(self.elapsed.microseconds))/1000000.0
        self.seconds = round(sectime,3)
        return self.seconds
