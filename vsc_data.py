import connector
import math

QUERY = '''
SELECT *
FROM PPD_DB.CAB.VC_CHASSIS
LIMIT 20
'''
# change the amount of days in the past relative to today, that the data pull will get
days = 365

# variables to hold the results
avg_interactions_per_day = -1.0
stdev_interactions_per_day = -1.0
avg_starts_per_day = -1.0
stdev_starts_per_day = -1.0
agent_daily_output = -1.0
effective_handle_time = -1.0

# data = connector.get_query(QUERY)

def __get_avg_interactions_table():
    global days
    
    query = '''
    -- Interactions per day, where count is higher than specified amount in the having clause.
    select 
        date(convert_timezone('UTC', 'America/Los_Angeles', A.CREATEDDATE)) as DATE,
        count(*) as DailyInteractionCount
    from 
        PPD_DB.SALESFORCE.AGENTWORK A 
        join (
            select u.id as userid
            from SALESFORCE.USER u
            left join SALESFORCE.USERROLE ur on u.userroleid = ur.id 
            where ur.id = '00E1W000001fgN1UAI' and u.isactive = TRUE
        ) U on A.USERID = U.USERID
    where
        A.CREATEDDATE >= dateadd(day, -{}, current_date())
    group by date(convert_timezone('UTC', 'America/Los_Angeles', A.CREATEDDATE))
        having count(*) > 500
    order by date(convert_timezone('UTC', 'America/Los_Angeles', A.CREATEDDATE));
    '''.format(days)
    
    return connector.get_data(query)


def __get_agent_starts_table():
    global days
    
    query = '''
    -- average agent starts per day
    SELECT DATE, COUNT(*) as NumberOfUsers
    FROM (
        SELECT 
            date(convert_timezone('UTC', 'America/Los_Angeles', A.CREATEDDATE)) as DATE,
            U.USERID,
            COUNT(*) as DailyInteractionCount
        FROM 
            PPD_DB.SALESFORCE.AGENTWORK A 
            INNER JOIN (
                SELECT u.id as userid
                FROM SALESFORCE.USER u
                INNER JOIN SALESFORCE.USERROLE ur ON u.userroleid = ur.id 
                WHERE ur.id = '00E1W000001fgN1UAI' 
            ) U ON A.USERID = U.USERID
        WHERE
            A.CREATEDDATE >= dateadd(day, -{}, current_date())
        GROUP BY 
            date(convert_timezone('UTC', 'America/Los_Angeles', A.CREATEDDATE)),
            U.USERID
        -- HAVING 
        --     COUNT(*) > 25
    ) 
    GROUP BY DATE
    HAVING COUNT(*) >= 10
    ORDER BY DATE;
    '''.format(days)
    return connector.get_data(query)

def fetch():
    """Gets the data based ont the queries that are defined above"""
    global avg_interactions_per_day, stdev_interactions_per_day
    global avg_starts_per_day, stdev_starts_per_day
    global agent_daily_output, effective_handle_time
    # interactions data
    idf = __get_avg_interactions_table()
    print(idf.head())

    avg_interactions_per_day = idf["DAILYINTERACTIONCOUNT"].mean()
    print("average interactions per day: ", avg_interactions_per_day)

    stdev_interactions_per_day = idf["DAILYINTERACTIONCOUNT"].std()
    print("stdev of interactions per day: ", stdev_interactions_per_day)

    # agent starts data
    sdf = __get_agent_starts_table()
    print(sdf.head())

    avg_starts_per_day = sdf["NUMBEROFUSERS"].mean()
    print("average starts per day: ", avg_starts_per_day)

    stdev_starts_per_day = sdf["NUMBEROFUSERS"].std()
    print("stdev of starts per day: ", stdev_starts_per_day)
    
    agent_daily_output = avg_interactions_per_day / avg_starts_per_day
    print("agent output per day: ", agent_daily_output)
    
    effective_handle_time = 480.0 / (avg_interactions_per_day / avg_starts_per_day)

if __name__=='__main__':
    fetch()