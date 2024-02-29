"""basic sim to try and get a grasp of making an oop sim with simpy"""

import simpy

class GasStation:

    def __init__(self, env, fill_up_time) -> None:
        
        self.env = env
        self.fill_up_time = fill_up_time
        self.pump = simpy.Resource(env, 1) # one pump resource

    def fill_up(self, car):
        
        yield self.env.timeout(self.fill_up_time) 
        print(f"Finished filling car {car} at {self.env.now:.2f}")

class SimDay:
    
    def __init__(self, env) -> None:
        
        self.env = env
        
        
class Car:
    
    def __init__(self, name) -> None:
        
        self.name = name
    
class Queue:
    
    def __init__(self, interval) -> None:
        
        self.interval = interval

def main():
    
    my_env = simpy.Environment()
    my_sim = SimDay()


if __name__ == "__main__":
    
    main()