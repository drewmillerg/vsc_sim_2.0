"""Represents the queue of customer's waiting to be processed in the call
    center"""

class WaitingQueue:

    def __init__(self):

        self.line = []

    def add_customer(self, customer):

        self.line.append(customer)

    def pop_customer(self):

        self.line.pop(0)