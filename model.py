from queue import Queue


class FakeEventGenerator:

    def __init__(self):
        self.events = Queue()

    # def add(self, event):


