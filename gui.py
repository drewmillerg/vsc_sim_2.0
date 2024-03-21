"""
GUI component which gives users the ability to interact with the 
event based simulation, and some forecasting functionality based on 
Snowflake data pulls.

Returns: Static, does not return an object. Opens a GUI and then closes it on exit.
"""

import PySimpleGUI as sg
import vsc_data as vd
import simulate as sm
import traceback


# use this to skip the Snowflake data pull.
mock_pull = False
tab = ' '
# single day sim run vars
agent_starts = 19
interactions = 1000
eht = 55

agent_starts_min = 17
agent_starts_max = 30



def data_pull_results():
    """Runs data pull and returns a string with the results."""
    global mock_pull
    
    if not mock_pull: vd.fetch()
    
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
    
    s1 = 'Showing data for the last {} days. Only days where the departments sees normal business volumes are included.\n\n'.format(vd.days)
    spacing = 100
    s1 += '{}{}\n'.format('Dept. Interactions Per Day:'.ljust(spacing), 'Agent Starts Per Day:'.ljust(spacing))
    s1 += '{}{}{}{}{}\n'.format('Avg: {}'.format(round(vd.avg_interactions_per_day, 2)).ljust(int(spacing/4)), 
                                'Stdev: {}'.format(round(vd.stdev_interactions_per_day, 2)).ljust(int(spacing/4)), 
                                "".rjust(int(50)),
                                'Avg: {}'.format(round(vd.avg_starts_per_day, 2)).ljust(int(spacing/4)),
                                'Stdev: {}'.format(round(vd.stdev_starts_per_day, 2)).ljust(int(spacing/4))
                                )
    s1 += '\n'
    s1 += '{}{}\n'.format('Agent Daily Output:'.ljust(spacing), 'Agent Effective Handle Time:'.ljust(spacing))
    s1 += '{}{}{}\n'.format('{} interactions'.format(round(vd.agent_daily_output, 2)).ljust(int(spacing/4)),
                            ''.rjust(76), 
                            '{} minutes'.format(round(vd.effective_handle_time, 2)).ljust(int(spacing/4)))
    
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
    [sg.Input(default_text='365', 
              key='-D-', 
              size=(20, 12))],
    [sg.Button('Start Data Pull')],
    [sg.Text('Snowflake data pull did not initiate.', key='-INTER-', visible=False)],
    
    # this doesn't produce accurate results, because of the way the SQL query works. 
    # It captures data for users that are in the dept, but that changes over time.
    # the historical volume reports must be used to calculate the volume growth.
    # # long term forecast functionality
    # [sg.Text('\nForecast Future Volume:')],
    # [sg.Text('Note- This query is fairly intensive.')],
    # [sg.Button('Forecast Volume Growth')],
    
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
    sg.Radio('Custom Run', 
              'rd1', 
              key='-CR-', 
              enable_events=True,
              visible=False),    
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
    
    [sg.Button('Run Simulation', key = '-SR5-', visible=False)],

    [sg.Text('Simulation Running...', key='-OUT-', visible=False)],
    [sg.Text('Sim Results (these are saved to "log.csv"):', key='-OUT0-', visible=False)],
    [sg.Multiline(key='-OUT1-', size=(1850, 300), visible=False)]
    ]
window = sg.Window('VSC Simulation', layout, size=(1280, 720), resizable=True, icon=sg.PSG_DEBUGGER_LOGO)

"""Hidden items"""
single_run_hidden = ['-R0-', '-R1-', '-R2-', '-R3-', '-R4-', '-R5-', '-R6-', '-R7-', '-R8-', '-R9-', '-R10-', '-FQ-']
spectrum_run_hidden = ['-SR5-']
custom_run_hidden = []
forecast_mode_hidden = []
output = ['-OUT0-', '-OUT1-']


"""Event loop"""
while True: 
    
    event, values = window.read()
    print(event, values)
    # close window
    if event == sg.WIN_CLOSED or event == 'Exit': break
    # run the forecast
    if event == 'Start Data Pull':
        # attempts the data pull and returns a helpfull error message if it failes.
        # program will still continue.
        vd.days = int(values['-D-'])
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
        for group in [spectrum_run_hidden, custom_run_hidden, forecast_mode_hidden]:
            for hidden in group:
                window[hidden].update(visible=False)
    # user wants to use query results for agent starts
    if event == '-R2-':
        sim_agent_starts = vd.avg_starts_per_day
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
        window['-R2-'].update(vd.avg_starts_per_day)
        window['-R4-'].update(vd.stdev_starts_per_day)
        window['-R6-'].update(vd.avg_interactions_per_day)
        window['-R8-'].update(vd.stdev_interactions_per_day)
        window['-R10-'].update(vd.effective_handle_time)
        
        
        
    
    """Spectrum run"""
    if event == '-SR-':
        for i in spectrum_run_hidden:
            window[i].update(visible=True)
        for group in [single_run_hidden, custom_run_hidden, forecast_mode_hidden]:
            for hidden in group:
                window[hidden].update(visible=False)
    # user runs the sim
    if event == '-SR5-':
        window['-OUT-'].update(visible=True)
        try:
            for i in output: window[i].update(visible=True)
            window.refresh()
            sm.spectrum_run()
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
    if event == '-FC-':
        for i in single_run_hidden:
            window[i].update(visible=True)
        
        
    """Start the sim"""
    if event == 'Run Simulation':
        # change the "output" element to be the value of "input" element
        print("placeholder for running the sim")
        
        
window.close()