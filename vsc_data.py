import connector
import math

QUERY = '''
SELECT *
FROM PPD_DB.CAB.VC_CHASSIS
LIMIT 20
'''
# change the amount of days in the past relative to today, that the data pull will get
DAYS = 90

# variables to hold the results
AVG_INTERACTIONS_PER_DAY = -1.0
STDEV_INTERACTIONS_PER_DAY = -1.0
AVG_STARTS_PER_DAY = -1.0
STDEV_STARTS_PER_DAY = -1.0
AGENT_DAILY_OUTPUT = -1.0
EFFECTIVE_HANDLE_TIME = -1.0

# data = connector.get_query(QUERY)

def get_interactions_table():
    global DAYS
    
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
    '''.format(DAYS)
    
    return connector.get_data(query)


def get_agent_starts_table():
    global DAYS
    
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
    '''.format(DAYS)
    return connector.get_data(query)

def fetch():
    """Gets the data based ont the queries that are defined above"""
    global AVG_INTERACTIONS_PER_DAY, STDEV_INTERACTIONS_PER_DAY
    global AVG_STARTS_PER_DAY, STDEV_STARTS_PER_DAY
    global AGENT_DAILY_OUTPUT, EFFECTIVE_HANDLE_TIME
    # interactions data
    idf = get_interactions_table()
    print(idf.head())

    AVG_INTERACTIONS_PER_DAY = idf["DAILYINTERACTIONCOUNT"].mean()
    print("average interactions per day: ", AVG_INTERACTIONS_PER_DAY)

    STDEV_INTERACTIONS_PER_DAY = idf["DAILYINTERACTIONCOUNT"].std()
    print("stdev of interactions per day: ", STDEV_INTERACTIONS_PER_DAY)

    # agent starts data
    sdf = get_agent_starts_table()
    print(sdf.head())

    AVG_STARTS_PER_DAY = sdf["NUMBEROFUSERS"].mean()
    print("average starts per day: ", AVG_STARTS_PER_DAY)

    STDEV_STARTS_PER_DAY = sdf["NUMBEROFUSERS"].std()
    print("stdev of starts per day: ", STDEV_STARTS_PER_DAY)
    
    AGENT_DAILY_OUTPUT = AVG_INTERACTIONS_PER_DAY / AVG_STARTS_PER_DAY
    print("agent output per day: ", AGENT_DAILY_OUTPUT)
    
    EFFECTIVE_HANDLE_TIME = 480.0 / (AVG_INTERACTIONS_PER_DAY / AVG_STARTS_PER_DAY)

if __name__=='__main__':
    fetch()