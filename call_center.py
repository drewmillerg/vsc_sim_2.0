import numpy as np
import simpy

class CallCenter:
    """ 
    Represents a call center or customer service center that takes calls or cases 
    """

    def __init__(self, env, num_employees, handle_time):
        self.env = env
        self.staff = simpy.Resource(env, num_employees)
        self.support_time = handle_time

    def support(self, customer):
        # time it takes to handle a call
        random_time = max(1, np.random.normal(self.support_time, 4)) # np.random.normal args (mean, standard dev)
        yield self.env.timeout(random_time)
        print(f"Support finished for {customer} at {self.env.now:.2f}")