import pandas as pd
import snowflake.connector as sc
import os

""" This tool connects to snowflake and can be used to query and store results in a dataframe. Pandas can then be used to create needed views/manipulations. 
- You must have a snowflake license on your PC user account profile
- Change the user variable to your windows login"""

# Add queries here as global variables
QUERY = '''
SELECT *
FROM PPD_DB.CAB.VC_CHASSIS
LIMIT 20
'''


def snowflake_connection():
    """Connects to Snowflake
        returns: Snowflake connection object"""
    myAcc = os.getlogin() + "@PACCAR.com"
    snowflake_conn = sc.connect(account='paccar',
                                user=myAcc,
                                database='ppd_db',
                                warehouse='ppd_small_wh',
                                authenticator="externalbrowser")

    return snowflake_conn


def get_data(query=None):
    """Runs the query and returns the resutls as a pandas dataframe"""
    print('Getting query from Snowflake connector...')
    snowflake_conn = snowflake_connection()
    
    if query == None: df = pd.read_sql_query(QUERY, snowflake_conn)
    else: df = pd.read_sql_query(query, snowflake_conn)
    snowflake_conn.close()
    
    # print("Query results head:\n" + df.head())
    # for name in df.columns:
    #     print(name)
    
    return df


if __name__ == '__main__':
    get_data()
