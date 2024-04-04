"""
GUI component which gives users the ability to interact with the 
event based simulation, and some forecasting functionality based on 
Snowflake data pulls.

Returns: Static, does not return an object. Opens a GUI and then closes it on exit.

Forecast mode:
    Should run the forecast, pop up the regression plot, give you the current average agent output and let you simulate future results
    
"""

import PySimpleGUI as sg
import vsc_data as vd
import forecast as fc
import simulate as sm
import traceback


# use this to skip the Snowflake data pull.
MOCK_PULL = False
TAB = ' '
# single day sim run vars
AGENT_STARTS = 19
INTERACTIONS = 1000
EHT = 55

# spectrum run sim vars
AGENT_STARTS_MIN = 17
AGENT_STARTS_MAX = 30


def data_pull_results() -> str:
    """Runs data pull and returns a string with the results."""
    global MOCK_PULL
    
    if not MOCK_PULL: vd.fetch()
    
    # s = 'Showing data for the last {} days. Only days where the departments sees normal business volumes are included.\n\n'.format(vd.days)
    # s += 'Interactions Per Day\n    Avg: {}    Stdev: {}'.format(
    #     round(vd.avg_interactions_per_day, 2),
    #     round(vd.stdev_interactions_per_day, 2),
    #     )
    # s += '\n\nAgent Starts Per Day\n    Avg: {}    Stdev: {}'.format(
    #     round(vd.avg_starts_per_day, 2),
    #     round(vd.stdev_starts_per_day, 2)
    #     )
    # s += '\n\nAverage Interactions that an agent completes in one day: {}'.format(
    #     round(vd.agent_daily_output, 2)
    #     )
    # s += '\n\nAgent Effective Handle Time (interactions per day/8 hours): {} minutes'.format(
    #     round(vd.effective_handle_time, 2)
    #     )
    
    s1 = 'Showing data for the last {} days. Only days where the departments sees normal business volumes are included.\n\n'.format(vd.DAYS)
    spacing = 100
    s1 += '{}{}\n'.format('Dept. Interactions Per Day:'.ljust(spacing), 'Agent Starts Per Day:'.ljust(spacing))
    s1 += '{}{}{}{}{}\n'.format('Avg: {}'.format(round(vd.AVG_INTERACTIONS_PER_DAY, 2)).ljust(int(spacing/4)), 
                                'Stdev: {}'.format(round(vd.STDEV_INTERACTIONS_PER_DAY, 2)).ljust(int(spacing/4)), 
                                "".rjust(int(50)),
                                'Avg: {}'.format(round(vd.AVG_STARTS_PER_DAY, 2)).ljust(int(spacing/4)),
                                'Stdev: {}'.format(round(vd.STDEV_STARTS_PER_DAY, 2)).ljust(int(spacing/4))
                                )
    s1 += '\n'
    s1 += '{}{}\n'.format('Agent Daily Output:'.ljust(spacing), 'Agent Effective Handle Time:'.ljust(spacing))
    s1 += '{}{}{}\n'.format('{} interactions'.format(round(vd.AGENT_DAILY_OUTPUT, 2)).ljust(int(spacing/4)),
                            ''.rjust(76), 
                            '{} minutes'.format(round(vd.EFFECTIVE_HANDLE_TIME, 2)).ljust(int(spacing/4)))
    
    return s1


"""Layout of window"""
sg.theme('Dark Blue 3')
layout = [
    # header
    [sg.Text('Welcome to the Vehicle Support Center Event Driven Simulation.', font=('Helvetica', 12, 'bold',), text_color='#FFDEAD')],
    [sg.Text('Choose from the options below to set up the simulation.')],
 
    # Snowflake data pull 
    [sg.Text('Data Pull for Independent Variables (not required but helpful).', font=('Helvetica', 11, 'bold'), text_color='#FFDEAD')],
    [sg.Text('How many days into the past do you want to include in the data pull? ')],
    [sg.Input(default_text='90', 
              key='-D-', 
              size=(20, 12))],
    [sg.Button('Start Data Pull')],
    [sg.Text('Snowflake data pull did not initiate.', key='-INTER-', visible=False)],
    
    # body 
    [sg.Text('What type of simulation run would you like to execute?', font=('Helvetica', 11, 'bold'), text_color='#FFDEAD')],
    # Radio Buttons for sim type
    [sg.Radio('Simulate a single day', 
              'rd1', 
              key='-R-', 
              enable_events=True),
    sg.Radio('Spectrum Run', 
             'rd1', 
             key='-SR-', 
             enable_events=True),
    sg.Radio('Forecast Mode', 
              'rd1', 
              key='-FC-', 
              enable_events=True)],    
    
    # options for single day run
    [sg.Radio('Fill using data from query', 'rd2', key='-FQ-', 
              enable_events=True, 
              visible=False)],   
    [sg.Text('Number of Agents: ', key='-R1-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-R2-', size=(10, 12), visible=False),  
     sg.Text('Stdev No. of Agents: ', key='-R3-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-R4-', size=(10, 12), visible=False),  
     sg.Text('Avg Interactions: ', key='-R5-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-R6-', size=(10, 12), visible=False),  
     sg.Text('Stdev Interactions: ', key='-R7-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-R8-', size=(10, 12), visible=False),  
     sg.Text('Effective Handle Time: ', key='-R9-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-R10-', size=(10, 12), visible=False),  
    ],
    [sg.Button('Run Simulation', key = '-R0-', visible=False)],

    # options for spectrum run
    [sg.Text('Min Number of Agents : ', key='-SR1-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-SR2-', size=(10, 12), visible=False, default_text="20"),  
     sg.Text('Max Number of Agents: ', key='-SR3-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-SR4-', size=(10, 12), visible=False, default_text="30"),
    ],  
    [sg.Text('Min Interactions: ', key='-SR5-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-SR6-', size=(10, 12), visible=False, default_text='800'),  
     sg.Text('Max Interactions: ', key='-SR7-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-SR8-', size=(10, 12), visible=False, default_text='1400'),
    ],  
    [sg.Text('Min Effective Handle Time (minutes): ', key='-SR9-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-SR10-', size=(10, 12), visible=False, default_text="8.5"),
     sg.Text('Max Effective Handle Time (minutes): ', key='-SR11-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-SR12-', size=(10, 12), visible=False, default_text="12.0"),    
    ],
    [sg.Text("*Note*: Spectrum runs can take anywhere from several seconds to a few minutes to complete because one day will be \n    simulated for EVERY combination of conditions, based on the input ranges provided.", visible=False, key='-SR13-', text_color='#FFFF00')],
    [sg.Button('Run Simulation', key = '-SR0-', visible=False),], 

    
    # options for forecast mode
    [sg.Text('''This mode will use machine learning to forecast future VSC interaction volumes, 
    and calculate the independent variables for the Simulation. It will then simulate 
    future department conditions, and tell you what is needed to reach the ASR goal.''', key='-FC0-', visible=False)],
    [sg.Button('Run ML Forecast', key = '-FC1-', visible=False),], 
    [sg.Text('Failed to load agent starts and agent output', key='-FC2-', visible=False)],
    [sg.Text('Min Number of Agents : ', key='-FC3-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-FC4-', size=(10, 12), visible=False, default_text="20"),  
     sg.Text('Max Number of Agents: ', key='-FC5-', visible=False, font=('Helvetica', 10, 'bold')),
     sg.Input(key='-FC6-', size=(10, 12), visible=False, default_text="30"),
    ],  
    [sg.Button('Start Simulation', key = '-FC7-', visible=False),], 
    
    [sg.Text('Simulation Running...', key='-OUT-', visible=False)],
    [sg.Text('Sim Results (these are saved to "log.csv"):', key='-OUT0-', visible=False)],
    # data output window
    [sg.Multiline(key='-OUT1-', size=(1850, 300), visible=False)],
    
    ]
window = sg.Window('VSC Simulation', layout, size=(1280, 720), resizable=True, icon=sg.PSG_DEBUGGER_LOGO)

"""Hidden items"""
single_run_hidden = ['-R0-', '-R1-', '-R2-', '-R3-', '-R4-', '-R5-', '-R6-', '-R7-', '-R8-', '-R9-', '-R10-', '-FQ-']
spectrum_run_hidden = ['-SR0-', '-SR1-', '-SR2-', '-SR3-', '-SR4-', '-SR5-', '-SR6-', '-SR7-', '-SR8-', '-SR9-', '-SR10-', '-SR11-', '-SR12-', '-SR13-']
forecast_mode_hidden = ['-FC1-', '-FC0-']
forecast_mode_additional = ['-FC2-','-FC3-','-FC4-','-FC5-','-FC6-','-FC7-',]
output = ['-OUT0-', '-OUT1-']


"""Event loop"""
while True: 
    
    event, values = window.read()
    print(event, values)
    # close window
    if event == sg.WIN_CLOSED or event == 'Exit': break
    # calculate independent variables.
    if event == 'Start Data Pull':
        # attempts the data pull and returns a helpfull error message if it failes.
        # program will still continue.
        vd.DAYS = int(values['-D-'])
        try: window['-INTER-'].update(data_pull_results()) 
        except Exception as e: 
            print(traceback.format_exc())
            print(e)
            window['-INTER-'].update("""The Snowflake Data pull process failed. This could be becasue you do not have a Snowflake license active on your account, or you do not have the proper permissions. 
            Please contact your IT administrator and ensure that you have required permissions to pull data from snowflake. 
            You can still use the simulation, however you will need to calculate the inputs manually.""") 
        window['-INTER-'].update(visible=True)
    
        
    """Single day run"""
    # user wants to do a single run
    if event == '-R-':
        for i in single_run_hidden:
            window[i].update(visible=True)
        for group in [spectrum_run_hidden, forecast_mode_hidden]:
            for hidden in group:
                window[hidden].update(visible=False)
    # user wants to use query results for agent starts
    if event == '-R2-':
        sim_agent_starts = vd.AVG_STARTS_PER_DAY
    # user runs the sim
    if event == '-R0-':
        ustarts = int(round(float(values['-R2-']), 0))
        uinter_mean = float(values['-R6-'])
        uhandle_mean = float(values['-R10-'])
        
        window['-OUT-'].update(visible=True)
        try: 
            for i in output: window[i].update(visible=True)
            window.refresh()
            sm.single_run(starts=ustarts, inter_mean=uinter_mean, handle_mean=uhandle_mean)
            window['-OUT-'].update("Simulation completed.")
        except Exception as e: 
            window['-OUT-'].update(visible=True)
            window['-OUT-'].update(str(e))
        window['-OUT1-'].update(sm.LOG_BUFFER)
        
    """Fill data from query"""
    if event == '-FQ-':
        window['-R2-'].update(vd.AVG_STARTS_PER_DAY)
        window['-R4-'].update(vd.STDEV_STARTS_PER_DAY)
        window['-R6-'].update(vd.AVG_INTERACTIONS_PER_DAY)
        window['-R8-'].update(vd.STDEV_INTERACTIONS_PER_DAY)
        window['-R10-'].update(vd.EFFECTIVE_HANDLE_TIME)
    
    """Spectrum run"""
    if event == '-SR-':
        for i in spectrum_run_hidden:
            window[i].update(visible=True)
        for group in [single_run_hidden, forecast_mode_hidden]:
            for hidden in group:
                window[hidden].update(visible=False)
    # user runs the sim
    if event == '-SR0-':
        min_agents = int(values['-SR2-']) 
        max_agents = int(values['-SR4-']) 
        min_inter = int(values['-SR6-']) 
        max_inter = int(values['-SR8-']) 
        min_handle = float(values['-SR10-']) 
        max_handle = float(values['-SR12-']) 
        window['-OUT-'].update(visible=True)
        try:
            for i in output: window[i].update(visible=True)
            window.refresh()
            sm.full_spectrum(handle_minutes_min=min_handle, handle_minutes_max=max_handle,
                             interactions_min=min_inter, interactions_max=max_inter,
                             agent_starts_min=min_agents, agent_starts_max=max_agents)
            window['-OUT-'].update("Simulation completed.")
        except Exception as e: 
            window['-OUT-'].update(visible=True)
            window['-OUT-'].update(str(e))
        window['-OUT1-'].update(sm.LOG_BUFFER)

    """Custom run"""
    if event == '-CR-':
        for i in single_run_hidden:
            window[i].update(visible=True)
            
    """Forecast mode"""
    # get the forecast, store the interactions array in a variable 
    # get the other independent variables, store them 
    # ask the user for range of agent starts, tell them where we currently sit
    # run the sim for the specified vars
    if event == '-FC-':
        for i in forecast_mode_hidden:
            window[i].update(visible=True)
    
    if event == '-FC1-':
        # run the regression
        df = fc.get_data()
        regressor, X_test, y_test = fc.train_model(df)
        y_pred = fc.predict_model(regressor, X_test, y_test)
        future_df = fc.future_forecast(regressor, df)
        
        # run data pull for other independent variables
        vd.DAYS = 90
        try: window['-INTER-'].update(data_pull_results()) 
        except Exception as e: 
            print(traceback.format_exc())
            print(e)
            window['-INTER-'].update("""The Snowflake Data pull process failed. This could be becasue you do not have a Snowflake license active on your account, or you do not have the proper permissions. 
            Please contact your IT administrator and ensure that you have required permissions to pull data from snowflake. 
            You can still use the simulation, however you will need to calculate the inputs manually.""") 
        window['-INTER-'].update(visible=True)
        # descriptive text for the user
        window['-FC2-'].update('Currently the VSC is averaging {} agent starts per day on a business day, and each agent is able to handle {} interactions in their shift. \nSee the regression plot window for the interaction forecast. \n Please enter the range (min and max) of agent starts that you want to simulate for the forecasted volumes.'.format(round(vd.AVG_STARTS_PER_DAY, 1), round(vd.AGENT_DAILY_OUTPUT, 1)))
        for i in forecast_mode_additional: window[i].update(visible=True)
        

        # plot the regression
        fc.plot_data(df['date_delta'].values.reshape(-1,1), df['DAILYINTERACTIONCOUNT'].values.reshape(-1,1), regressor, future_df) 
        
    if event == '-FC7-':
        min_agents = int(values['-FC4-'])
        max_agents = int(values['-FC6-'])
        min_handle = vd.EFFECTIVE_HANDLE_TIME
        max_handle = vd.EFFECTIVE_HANDLE_TIME
        
        arr = future_df['predicted_interactions']
        window['-OUT-'].update(visible=True)
        try:
            for i in output: window[i].update(visible=True)
            window.refresh()
            sm.forecast_spectrum(interaction_forecast=arr,
                             handle_minutes_min=min_handle, handle_minutes_max=max_handle,
                             agent_starts_min=min_agents, agent_starts_max=max_agents)
            window['-OUT-'].update("Simulation completed.")
        except Exception as e: 
            window['-OUT-'].update(visible=True)
            window['-OUT-'].update(str(e))
        window['-OUT1-'].update(sm.LOG_BUFFER)
        
        
window.close()