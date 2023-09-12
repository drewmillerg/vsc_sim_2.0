import numpy as np
import pandas as pd

def generate_call_distribution(peak_hours_start, peak_hours_end, avg_calls_per_day, std_calls_per_day):
    day_hours = np.arange(24)
    call_distribution = np.zeros(24)
    call_distribution[peak_hours_start:peak_hours_end] = np.random.normal(1, 0.3, peak_hours_end-peak_hours_start)
    call_distribution = np.interp(day_hours, np.linspace(0, 23, peak_hours_end-peak_hours_start), call_distribution)
    call_distribution /= call_distribution.sum()
    calls_per_hour = np.random.normal(avg_calls_per_day/24, std_calls_per_day/24, 24)
    calls_per_hour *= call_distribution
    calls_per_hour = np.round(calls_per_hour).astype(int)
    return calls_per_hour

def initialize_agents(num_agents, peak_hours_start, peak_hours_end, shift_length):
    agents = []
    for i in range(num_agents):
        shift_start = np.random.choice(np.arange(peak_hours_start-shift_length+1, peak_hours_end-shift_length+1))
        agents.append({'status': 'available', 'finish_time': shift_start*60})
    return agents

def assign_calls_to_agents(call_queue, agents, avg_call_duration, std_call_duration):
    call_data = []
    for agent in agents:
        if agent['status'] == 'busy' and agent['finish_time'] <= hour*60:
            agent['status'] = 'available'
        
        if len(call_queue) == 0:
            continue
        
        if agent['status'] == 'available':
            call_id = call_queue.pop(0)
            call_duration = np.random.normal(avg_call_duration, std_call_duration)
            agent['status'] = 'busy'
            agent['finish_time'] += call_duration
            call_data.append({'hour': hour, 'call_id': call_id, 'agent': agents.index(agent), 'start_time': agent['finish_time']-call_duration, 'finish_time': agent['finish_time']})
    return call_data

def run_simulation(num_agents, shift_length, peak_hours_start, peak_hours_end, avg_call_duration, std_call_duration, avg_calls_per_day, std_calls_per_day):
    agents = initialize_agents(num_agents, peak_hours_start, peak_hours_end, shift_length)
    call_queue = []
    call_data = []

    for hour in range(24):
        calls_per_hour = generate_call_distribution(peak_hours_start, peak_hours_end, avg_calls_per_day, std_calls_per_day)
        call_queue += [call_id for call_id in range(len(call_queue), len(call_queue) + calls_per_hour[hour])]
        call_data += assign_calls_to_agents(call_queue, agents, avg_call_duration, std_call_duration)

    df = pd.DataFrame(call_data)
    return df

def main():
    num_agents = 20
    shift_length = 8 # in hours
    peak_hours_start = 4 # in hours
    peak_hours_end = 16 # in hours
    avg_call_duration = 10.4 # in minutes
    std_call_duration = 2 # in minutes
    avg_calls_per_day = 850
    std_calls_per_day = 30

    call_data = run_simulation(num_agents, shift_length, peak_hours_start, peak_hours_end, avg_call_duration, std_call_duration, avg_calls_per_day, std_calls_per_day)
    call_data.to_csv('log.csv', index=False)

if __name__ == '__main__':
    main()