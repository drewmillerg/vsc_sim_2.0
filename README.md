This project functions to forcast the capacity and ASR of the Vehicle Support
Center. This is accomplished by first measuring and forecasting some independent
variables: 

    - Average customer volume per day (interactions).
    - Average number of interactions handled per agent per day.
        This must only be measured for agents and days where there is a backlog of 
        cases, so that we can see what true agent productive capacity is.
    - Average number of agents that will work a shift in any given weekday.
        A buffer should be built in to this number to account for the average 
        number of agents that are expected to be out on vacation, sick or training. 

Once these numbers are calculated, they are entered into the event-based 
simulation, which simulates 24 hour department workdays. In the simulation 
customers and agents shifts follow a distribution throughout the day.

The simulation logs the simulated performance of the department in log.csv.
This data is then used to forecast the future ASR for different staffing levels
in the department.
