Sensitivity analysis 

    limitations:
        Sensitivity analysis relies upon historical data and makes assumptions 
            about the mathematical relationships between the independent and 
            dependent variables
        Why is this a big limitation for VSC? Because there are so many dimensions 
            of independent variables (customer arrival dist, agent shift dist, 
            residual waiting interactions, specialists, case volumes, types of 
            cases and thus handle times, agent skill level)


Erlang C formula 

    benefits:
        give an estimate of 

    assumptions:
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

    limitations:
        Our findings indicate that the Erlang C model is subject to significant error in predicting system performance, but that these errors are heavily biased and most likely to be pessimistic, i.e. the system tends to perform better than predicted. It may be the case that the model's tendency to provide pessimistic (i.e. conservative) estimates helps explain its continued popularity. Prediction error is strongly correlated with the abandonment rate so the model works best in call centers with large numbers of agents and relatively low utilization rates (Robbins, Thomas & Medeiros, Deuzilene & Harrison, Terry).
    

Sim 
    
    benefits:
        Scope - Erlang and sensitivity analysis deal with small scope and 
            assumptions which can change. The sim is mathematically accurate
            representation of the significant variables interacting with eachother.

        Accuracy - Sim doesn't rely on correctly defined mathematical relationships
            between dependent and independent variables. It only relies on the 
            independent variables to be correct.


Sources:

Robbins, Thomas & Medeiros, Deuzilene & Harrison, Terry. (2010). Does the Erlang C model fit in real call centers?. Proceedings - Winter Simulation Conference. 2853-2864. 10.1109/WSC.2010.5678980. 
