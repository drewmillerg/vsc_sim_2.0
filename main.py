"""
Simulation of Vehicle Support Center operations (24hr).

Sensitivity analysis benefits
    Sensitivity analysis relies upon historical data and makes assumptions 
        about the mathematical relationships between the independent and 
        dependent variables
    Why is this a big limitation for VSC? Because there are so many dimensions 
        of independent variables (customer arrival dist, agent shift dist, 
        residual waiting interactions, specialists, case volumes, types of 
        cases and thus handle times, agent skill level)

Erlang C formula assumptions (limitations):
    The customer requests follow a Poisson arrival process (number of events over a given period of time):
    The number of customers is large.
    The impact of a single customer has minimal impact on the overall system performance.
    All customers use the system independently of others.
    Service times are exponentially distributed.
    Customers never abandon any service request while waiting for a support agent.
    All lost calls are not abandoned, but simply delayed.
    A support agent handles only one customer exclusively for the specified period.
    The total number of support resources is lower than the number of 
        customers.

Sim benefits
    Scope - Erlang and sensitivity analysis deal with small scope and 
        assumptions which can change. The sim is mathematically accurate
        representation of the significant variables interacting with eachother.
    Accuracy - Sim doesn't rely on correctly defined mathematical relationships
        between dependent and independent variables. It only relies on the 
        independent variables to be correct.
        
    

Requirements:
    Must be able to simulate 24 hours
    Must be able to simulate the calls coming in on a definable distribution
    Must be able to simulate the shifts starting at defined times
    Must be able to simulate the whole week
    ASR calculation must be an average of each interaction, NOT the average 
        of the day to day ASR

Open issues:
    - CUSTOMERS_BEING_HELPED array is not tracking correctly
        only holding one customer at a time
"""

"""
Todo: 
- (fixed 8/3/23) wait times from previous hour are not carrying over to next hour.
- (bug) Remove processing time from partial customer processing at hour transition.
    -After fixing this the correction coefficients need to be rechecked and probably removed.
- (bug) agent resources goes to 0 during stress test with low agents available, 
    throws simpy resource error.
- Write unit tests.
"""

import random
import traceback
import simpy
import numpy as np
import pandas as pd
import datetime
import csv
import math
# from customer import Customer
# from waiting_queue import WaitingQueue
# from call_center import CallCenter



""" Global vars
All of the time related variables are in seconds, and outputs converted to 
minutes later when data is recorded/displayed.
"""

"""
------- Set these vars based on current real world data
"""
# if this is enabled,  dependent variable will be randomized based on their
#   mean and stdev. Otherwise only the mean will be used. 
ENABLE_DISTRIBUTIONS = False
# agent starts pe
# r day
AGENT_STARTS = 20
# stats about the interactions that VSC handless in a day (calculate based on 
# stat analysis)
INTERACTIONS_MEAN = 950
INTERACTIONS_STDEV = 40
# in seconds (480 sec = 8 min) 10.6min = 640 sec, effective handle time, 
#   based on 45 interaction per agent. This was the average as of 2/8/23 with
#   our heaviest volumes
HANDLE_TIME_MEAN = 9.17
HANDLE_TIME_STDEV = .083
# dictionary for setting the proportion of customer interactions that come
#   in for each hour. 
#       Must add up to 1
WORK_PORTIONS = {
    '0': .002, '1': .002, '2': .005, '3': .008, '4': .026, '5': .053,
    '6': .080, '7': .099, '8': .101, '9': .102, '10': .099, '11': .103,
    '12': .099, '13': .073, '14': .046, '15': .033, '16': .024, '17': .015,
    '18': .010, '19': .007, '20': .004, '21': .003, '22': .003, '23': .003
}
# portion of the agents that you want working per hour. 
#   Must add up to 1
AGENT_PORTIONS = {
    '0': .04, '1': .04, '2': .04, '3': .09, '4': .18, '5': .4,
    '6': .57, '7': .62, '8': .74, '9': .79, '10': .84, '11': .88,
    '12': .84, '13': .75, '14': .57, '15': .4, '16': .31, '17': .22,
    '18': .22, '19': .13, '20': .09, '21': .09, '22': .04, '23': .04   
}



"""
---- These vars are used during runtime for tracking and calculations.
     DO NOT hardcode these variables.
"""
START = datetime.datetime.now()
AGENT_NO = 0
# tracks the agents currently working
#   key is int tracking the agent that is starting
AGENTS_WORKING = {}
# tracks the number of agents that are available to work the rest of the day
BENCH = -1
# this is set for the day by the setter function
INTERACTIONS_TODAY = 0
# Customer interaction intervals are on a normal dist based on trailing 30 day 
#   data
# CUSTOMER_INTERVAL = 33 # how often customer interactions flow in, cases/ 
#   calls come in every 33 seconds in this case, corresponds to about 872 interactions
CUSTOMER_INTERVAL = 0
HOUR_INTERVAL = 0
# tracks the current customer number
CUSTOMER_NUM = 0
# 60 seconds * 60 minutes = 1 hour
SIM_TIME = 60 * 60
CURRENT_HOUR = 0
WAIT_TIMES = []
CUSTOMERS_HANDLED = 0
CURRENT_HOUR = 0
# set by a setter, based on the mean and stdev given. will be represented in seconds.
HANDLE_TIME = -1
# 2d list containing the customers waiting at any given time. 
# each element is a list of size 2, where:
# [0] is the name
# [1] is the time they entered the waiting queue, relative to the beginning of the hour
CUSTOMERS_WAITING = []
# 2d list where each element is a list [customer name, env time that help began]
CUSTOMERS_BEING_HELPED = []
# the wait times for the customers that did not get processed last hour
RESIDUAL_WAIT_TIMES = []
# most recent customer to enter the waiting queue, who was already in the queue when the hour started.
PREV_HOUR_CUTOFF_CUST = 0



class CallCenter:
    """ 
    Represents a call center or customer service center that takes calls or cases.
    Container for an env, staff resources, and handle time 
    """

    def __init__(self, env, num_employees, handle_time):
        self.env = env
        self.staff = simpy.Resource(env, num_employees)
        self.support_time = handle_time

    def support(self, customer, opt_handle_time=None):
        # time it takes to handle a call.
        if opt_handle_time == None:
            yield self.env.timeout(self.support_time)
            print(f"Support finished for {customer} at {self.env.now/60:.2f}")
        # if an argument for the handle time is not given, use the global 
        #   handle time. Else use the given handle time.
        else:
            yield self.env.timeout(opt_handle_time)
            print(f"Support finished for {customer} at {self.env.now/60:.2f}")



def set_handle_time():
    """
    Setter for handle time.
    """
    global HANDLE_TIME
    
    if ENABLE_DISTRIBUTIONS:
        mean = int(HANDLE_TIME_MEAN * 60)
        stdev = int(HANDLE_TIME_STDEV * 60)
        HANDLE_TIME = int(np.random.normal(mean, stdev, 1))
    
    else: HANDLE_TIME = int(HANDLE_TIME_MEAN * 60)



def set_agents_working(hour=12):
    """
    Setter for AGENTS_WORKING
    This will be used to determine how many agents are working, each time the
        simulation simulates an hour.

    TODO: make the number of employees returned dynamic, based on the number 
            of total agent starts and the time of day.
    """
    
    global CURRENT_HOUR, AGENT_NO, AGENTS_WORKING, BENCH
    # simplified version
    # AGENTS_WORKING = 18

    # filling the bench
    if CURRENT_HOUR == 0:
        # subtracting 1 to account for the night agent
        BENCH = AGENT_STARTS -1

    # setting up AGENTS_WORKING for off hours
    # if it's earler than 3 am, night agent from previous day will be working
    if CURRENT_HOUR < 3:
        if CURRENT_HOUR == 0:
            add_agent(4, -1)
        else:
            decrement_agent_hours_left()

    # if it's later than 9 pm
    elif CURRENT_HOUR > 21:
        # if it's 10 pm, there is one agent and they have 2 hours left 
        if CURRENT_HOUR == 22:
            AGENTS_WORKING = {-1: 2}
        else:
            decrement_agent_hours_left()

    # hours between 3 am and 9 pm inclusive
    else:
        previous_agent_count = get_agents_working_count()
        decrement_agent_hours_left()
        ideal_agents_working = int(AGENT_STARTS * AGENT_PORTIONS[str(CURRENT_HOUR)])
        print("Ideal number of agents working:", ideal_agents_working)
        ideal_agents_added = ideal_agents_working - previous_agent_count

        # case where staff and caseload are ramping up
        if ideal_agents_working > get_agents_working_count():
            # case where there are enough agents on the bench to fill the needed workcload
            if ideal_agents_added <= BENCH:
                for i in range(ideal_agents_added):
                    add_agent()

            # case where there are not enough on the bench for ideal workload
            elif ideal_agents_added > BENCH:
                for i in range(BENCH):
                    add_agent()
    
    print("On bench:", BENCH)
    # for agent in AGENTS_WORKING:
    #     print("Agent", agent, "has", AGENTS_WORKING[agent], "hours left." )
    
    # case where there are not enough agents and so capacity is running at 
    #   minimum
    if AGENTS_WORKING == 0:
        print("You ran out of agent resources. Work is now running with 1 staff resource.")
        AGENTS_WORKING = 1
                

    
def add_agent(hours_left = 8, this_agent = 0):
    """
    Adds one agent to the dict of currently working agents.
        if this_agnet variable is left default it means that this is the first
        agent of the day (technically started yesterday), which is why the 
        AGENT_NO does not get incremented.
    """
    
    global AGENT_NO
    global AGENTS_WORKING
    global BENCH
    # default adds an agent to AGENTS_WORKING
    if this_agent == 0:
        print("Added agent", AGENT_NO, "to AGENTS_WORKING, with", hours_left, "hours left.")
        AGENT_NO += 1
        AGENTS_WORKING[AGENT_NO] = hours_left
        BENCH -= 1
    # adds specific agent
    else:
        print("Added agent", this_agent, "to AGENTS_WORKING, with", hours_left, "hours left.")
        AGENTS_WORKING[this_agent] = hours_left



def decrement_agent_hours_left():
    """
    Subtracts an hour from the time each agent has left to work
    if the time they have left is 0, it removes them.
    """
    global AGENTS_WORKING 
    
    for i in tuple(AGENTS_WORKING):
        try:
            if AGENTS_WORKING[i] == 0:
                del AGENTS_WORKING[i]
            else:
                AGENTS_WORKING[i] -=1
        except:
            print("Error: Out of bounds", i, "for AGENTS_WORKING dict.")
            continue



def get_agents_working_count():
    """
    Getter for AGENTS WORKING
    """
    print("Agents working:", len(AGENTS_WORKING))
    return len(AGENTS_WORKING)



def day_customer_interval(hour=12):
    """
    Provides the interval upon which the work comes in for a given sim 
        execution.

    Returns: int representing the number of seconds between customer 
        interactions coming in overall for an entire day.
    """
    global INTERACTIONS_MEAN, INTERACTIONS_STDEV, CUSTOMER_INTERVAL

    interactions = int(
        np.random.normal(INTERACTIONS_MEAN, INTERACTIONS_STDEV, 1))
    day_seconds = 60 * 60 * 12
    CUSTOMER_INTERVAL = int(day_seconds / interactions)

    return CUSTOMER_INTERVAL



def hour_customer_interval(hour=12):
    """
    Provides the interval upon which the work comes in for a given hour.
    Assumes: 
        INTERACTIONS_TODAY has been set.
        CURRENT_HOUR has been set.

    Returns: int representing the number of seconds between customer 
        interactions coming in.
    """
    global HOUR_INTERVAL
    # correcting for rounding error in final amount of customers handled
    correction_coefficient = 1.0112
    # correction_coefficient = 1
    interactions_this_hour = int(
        (INTERACTIONS_TODAY * WORK_PORTIONS[str(CURRENT_HOUR)]) * correction_coefficient)
    print("Interactions for hour", CURRENT_HOUR, " are:", interactions_this_hour)
    HOUR_INTERVAL = int(3600 / interactions_this_hour)
    print("Customer interval for this hour is:", HOUR_INTERVAL, "seconds.")
    return HOUR_INTERVAL



def set_interactions_today():
    global INTERACTIONS_TODAY

    if ENABLE_DISTRIBUTIONS:
        INTERACTIONS_TODAY = int(
            np.random.normal(INTERACTIONS_MEAN, INTERACTIONS_STDEV, 1))
    
    else: INTERACTIONS_TODAY = INTERACTIONS_MEAN
    
    

def customer(env, call_center, wait_time=0):
    """ 
    Represents a customer interaction

    wait_time: int representing the number of seconds the customer has been 
        waiting.
    """
    global CUSTOMERS_HANDLED, CUSTOMERS_WAITING, CUSTOMER_NUM, CUSTOMERS_BEING_HELPED

    
    # print("Current day: ", get_day(env))
    CUSTOMER_NUM += 1
    name = CUSTOMER_NUM
    wait_start = (env.now - wait_time)
    print(f"Customer {name} enters waiting queue at {wait_start/60:.2f}!")
    # adding a customer to the list waiting
    # 2d array that holds the cust name, their wait time if they are still in 
    #    the waiting queue

    # only add cust to waiting if they were not already waiting
    if wait_start >= 0:
        CUSTOMERS_WAITING.append([name, SIM_TIME - wait_start])
        print(f"CUSTOMERS_WAITING size after adding customer = {len(CUSTOMERS_WAITING)}")
        # print_customers_waiting()

    with call_center.staff.request() as request:
        yield request

        print(f"Customer {name} enterscall at {env.now/60:.2f}")
        # add customer to the being-helped list
        if len(CUSTOMERS_BEING_HELPED) == 0:
            CUSTOMERS_BEING_HELPED.append([name, int(SIM_TIME - env.now)])
            
        elif name < CUSTOMERS_BEING_HELPED[0][0] or name > CUSTOMERS_BEING_HELPED[-1][0]:
            CUSTOMERS_BEING_HELPED.append([name, int(SIM_TIME - env.now)])
            
        # if customer was already being helped, subtract the time they've been helped from the 
        #   time it takes to help them. Otherwise use the global handle time.
        if env.now == 0:
            for cust in CUSTOMERS_BEING_HELPED:
                # if cust is being helped and they didn't enter queue at the beginning of this hour:
                if cust[0] == name:
                    if cust[1] != 3600:
                        yield env.process(call_center.support(name, HANDLE_TIME - cust[1])) 
                        break
                    
                    else:
                        yield env.process(call_center.support(name))
                        
                    
        else:
            yield env.process(call_center.support(name))   

        wait_end = env.now
        print(f"Customer {name} left call at {env.now/60:.2f}")
        print(f"Removing customer {CUSTOMERS_WAITING[0][0]} from waiting array")
        CUSTOMERS_WAITING.pop(0)
        CUSTOMERS_BEING_HELPED.pop(0)
        print(
            f"CUSTOMERS_WAITING size after removing customer = {len(CUSTOMERS_WAITING)}")

        speed_to_respond = wait_end - wait_start
        WAIT_TIMES.append(speed_to_respond)
        print(f"Speed to respond: {speed_to_respond / 60:.2f}")
        CUSTOMERS_HANDLED +=1



def print_customers_waiting():
    global CUSTOMERS_WAITING
    
    print("Waiting: [ ", end="")
    for cust in CUSTOMERS_WAITING:
        print(" [ ", end="")
        for i in cust:
            print(f" {i} ", end="")
        print(" ] ", end="")
    print(" ]")



def run_sim(env, num_employees, handle_time, customer_interval, waiting=2):
    """
    Runs the simulation, simulates one hour per execution. 
    """
    global CUSTOMERS_WAITING
    global CUSTOMER_NUM
    global PREV_HOUR_CUTOFF_CUST
    
    # this is used so that customers who have been waiting more than 
    #   1 hour can have another hour added to their wait time.
    first_customer_this_hour = CUSTOMER_NUM + len(CUSTOMERS_WAITING) + 1
    print(f"First customer this hour: {first_customer_this_hour}")
    
    # accounting for additional hours that customers have been waiting
    try:
        for i in range(first_customer_this_hour -1):
            CUSTOMERS_WAITING[i][1] += 3600
            
    except:
        pass
    
    # showing the customers waiting
    print("Customers waiting:", len(CUSTOMERS_WAITING))

    call_center = CallCenter(env, num_employees, handle_time)

    # the range is the number of customers that are already waiting
    # for 5 waiting, you would do range(1,6)
    if len(CUSTOMERS_WAITING) == 0:
        for i in range (1, 2):
            env.process(customer(env, call_center))
            
    else:
        for i in range (1, len(CUSTOMERS_WAITING)+1):
            env.process(customer(env,  call_center, 
                                 CUSTOMERS_WAITING[i-1][1] - 3600))
            
    while True:
        yield env.timeout(random.randint(customer_interval - 1, 
                                         customer_interval + 1))
        
        try:
            i += 1
        except: i = 1
        
        this_customer = customer(env, call_center)
        env.process(this_customer)
        # if env.now() == SIM_TIME:
        

    
def clear_tracking_vars():
    """This is so that the sim can be run multiple times in one execution"""
    global CUSTOMER_NUM, CUSTOMERS_BEING_HELPED, CUSTOMERS_WAITING 
    global CUSTOMERS_HANDLED, WAIT_TIMES, RESIDUAL_WAIT_TIMES
    global PREV_HOUR_CUTOFF_CUST, WAIT_TIMES
    
    CUSTOMER_NUM = 0
    CUSTOMERS_BEING_HELPED = []
    CUSTOMERS_WAITING = []
    CUSTOMERS_HANDLED = 0
    RESIDUAL_WAIT_TIMES = []
    PREV_HOUR_CUTOFF_CUST = 0
    WAIT_TIMES = []
    


def simulate_day():
    """runs the sim for 24 hours, tracking the necessary variables"""
    global CURRENT_HOUR, CUSTOMERS_WAITING, CUSTOMER_NUM
    set_interactions_today()
    clear_tracking_vars()
    set_handle_time()

    for i in range(0, 24):
        
        CURRENT_HOUR = i
        set_agents_working()
        my_env = simpy.Environment()
        interval = hour_customer_interval(CURRENT_HOUR)
        agent_count = get_agents_working_count()
        my_env.process(run_sim(my_env, agent_count, HANDLE_TIME, interval))
        my_env.run(until=SIM_TIME)
        # subtracting the waiting customers from the customer num, so that when
        #   they are added to the next hour, they have the correct name.
        CUSTOMER_NUM -= len(CUSTOMERS_WAITING)
        print("Hour", CURRENT_HOUR, "ending.")
        # logging and displaying data
        print("Customers handled: " + str(CUSTOMERS_HANDLED))
        my_df = hour_to_df()
        asr = get_asr()
        print(f"ASR: {asr:.2f}")
        print(my_df.head())
        # log_data(my_df)
    
    day_df = day_to_df()
    log_data(day_df)



def max_output_possible():
    """
    Computes the number of interactions that could have been handled during
        the simulation.
    """
    return AGENT_STARTS * SIM_TIME / HANDLE_TIME



def get_utilization():
    """
    Computes the actual utilization
    
    Assumes: 
        - the sim has completed the day, so that all of the customers that 
        will be helped, have been helped.
        - all employees work an 8 hour shift
        
    """
    # full capacity is the amount of customers that entered, minus the ones that entered during
    #   one unit of handle time.
    
    # amount of labor time available
    # correction for rounding error
    # correction = .95
    correction = 1.0
    labor_time = 60 * 60 * 8 * AGENT_STARTS
    customers_possible = int(labor_time / HANDLE_TIME)
    util = CUSTOMERS_HANDLED / (customers_possible * correction)

    if util > 0.95:
        return 1.0
    else:
        return util



def get_asr():
    """
    Computes Average Speed to Respond
    Must be called after the sim has completed.
    Return: float
    """
    
    return sum(WAIT_TIMES) / len(WAIT_TIMES) / 60



def hour_to_df():
    """
    Creates dataframe with the inputs and outputs of each sim run
        Pass in the number of customers (interactions) handled
    """

    columns = [
        
        "Agent Starts Label",
        "Agent Starts",
        "Agents Working Label",
        "Agents Working",
        "Sim Hour Label", 
        "Sim Hour", 
        "Interactions Today Label", 
        "Interactions Today", 
        "Interactions Handled Label",
        "Interactions Handled",
        "ASR Label", 
        "ASR", 
        "Timestamp Label", 
        "Timestamp"
    ]

    df = pd.DataFrame(columns=columns, index=[0])
    
    df["Agent Starts Label"] = " AgntStrts: "
    df["Agent Starts"] = AGENT_STARTS
    df["Agents Working Label"] = " AgntsWkng: "
    df["Agents Working"] = get_agents_working_count()
    df["Sim Hour Label"] = " SimHr: "
    df["Sim Hour"] = round(CURRENT_HOUR)
    df["Interactions Today Label"] = " EstInteractns: "
    df["Interactions Today"] = INTERACTIONS_TODAY
    df["Interactions Handled Label"] = " InteractnsHndld: "
    df["Interactions Handled"] = CUSTOMERS_HANDLED
    df["ASR Label"] = " ASR: "
    df["ASR"] = round(get_asr(), 2)
    df["Timestamp Label"] = " Tmestmp: "
    df["Timestamp"] = datetime.datetime.now().strftime(
        'X%m/X%d/%Y X%H:X%M:X%S').replace('X0','X').replace('X','')    

    return df



def day_to_df():
    """
    Creates dataframe with the inputs and outputs of each sim run
        Pass in the number of customers (interactions) handled
    """
    
    columns = [
        
        "Agent Starts Label",
        "Agent Starts",
        "Interactions Today Label", 
        "Interactions Today", 
        "Interactions Handled Label",
        "Interactions Handled",
        "Handle Time Label",
        "Handle Time",
        "ASR Label", 
        "ASR", 
        "Utilization Label",
        "Utilization",
        "Timestamp Label", 
        "Timestamp"
    ]

    df = pd.DataFrame(columns=columns, index=[0])
    
    df["Agent Starts Label"] = " AgntStrts: "
    df["Agent Starts"] = AGENT_STARTS
    df["Interactions Today Label"] = " EstInteractns: "
    df["Interactions Today"] = INTERACTIONS_TODAY
    df["Interactions Handled Label"] = " InteractnsHndld: "
    df["Interactions Handled"] = CUSTOMERS_HANDLED
    df["Handle Time Label"] = " HndlTme: "
    df["Handle Time"] = round(HANDLE_TIME / 60, 2)
    df["ASR Label"] = " ASR: "
    df["ASR"] = round(get_asr(), 2)
    df["Utilization Label"] = " EstUtil: "
    df["Utilization"] = round(get_utilization(), 2)
    df["Timestamp Label"] = " Tmestmp: "
    df["Timestamp"] = datetime.datetime.now().strftime(
        'X%m/X%d/%Y X%H:X%M:X%S').replace('X0','X').replace('X','')    

    return df



def log_data(df):
    """
    logs the inputs and outputs from the hour in the "log.csv" file, for 
        later analysis
    """
    df.to_csv('log.csv', mode='a', index=False, header=False)



def main():
    
    # # running the sim
    # print("Starting Call Center Simulation")
    # simulate_day()

    
    try:
        # running the sim
        print("Starting Call Center Simulation")
        simulate_day()

    except ValueError as ve:
        print("\nError: You may have run out of agents for the day\n")
        traceback.print_exception()
    except: 
        print("An unhandled error ocurred during this run of the simulation.")
        traceback.print_exception()
        
        
        
def full_spectrum():
    """Runs the sim in the full range of dependent variables
        -Note: This can take a very long time, because it is essentially O(n^3)
            where n is the number of steps through each variable loop
        """
    global ENABLE_DISTRIBUTIONS, HANDLE_TIME_MEAN, INTERACTIONS_MEAN
    global AGENT_STARTS, INTERACTIONS_STDEV, HANDLE_TIME_STDEV
    
    # edit these ranges and run to do full spectrum testing    
    ENABLE_DISTRIBUTIONS = False
    
    handle_minutes_min = 8.5
    handle_minutes_max = 11
    step_minutes = .5
    HANDLE_TIME_STDEV = .083
    
    interactions_min = 800
    interactions_max = 1200
    interactions_step = 50
    INTERACTIONS_STDEV = 40
    
    agent_starts_min = 17
    agent_starts_max = 25
    
    start = int(handle_minutes_min * 60)
    stop = int(handle_minutes_max * 60)
    step = int(step_minutes * 60)
    for i in range(start, stop, step):
        HANDLE_TIME_MEAN = i/60
        
        for j in range(interactions_min, interactions_max, interactions_step):
            INTERACTIONS_MEAN = j
                    
            for k in range(agent_starts_min, agent_starts_max):
                AGENT_STARTS = k
            
                for l in range(0,1):
                    main()    
                    
                    
                    
def single_run():
    """Runs the sim a single time"""
    global ENABLE_DISTRIBUTIONS, HANDLE_TIME_MEAN, INTERACTIONS_MEAN
    global AGENT_STARTS, INTERACTIONS_STDEV, HANDLE_TIME_STDEV
    
    ENABLE_DISTRIBUTIONS = False
    # agent starts pe
    # r day
    AGENT_STARTS = 16
    # stats about the interactions that VSC handless in a day (calculate based on 
    # stat analysis)
    INTERACTIONS_MEAN = 950
    INTERACTIONS_STDEV = 40
    # in seconds (480 sec = 8 min) 10.6min = 640 sec, effective handle time, 
    #   based on 45 interaction per agent. This was the average as of 2/8/23 with
    #   our heaviest volumes
    HANDLE_TIME_MEAN = 9.17
    HANDLE_TIME_STDEV = .083
    
    main()
    


if __name__ == "__main__":
    """Use this as a driver script"""
    
    # testing
    single_run()
    # full_spectrum()
    
    