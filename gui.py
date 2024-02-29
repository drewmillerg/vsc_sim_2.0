import PySimpleGUI as sg
# Processing function

def makeSubLists(s):

    if "\n" in s:
        l = s.split("\n")
    elif ",  " in s:
        l = s.split(",  ")
    elif ", " in s:
        l = s.split(", ")
    elif "," in s:
        l = s.split(",")
    elif " " in s:
        l = s.split(" ")

    X = len(l[0])
    NMACROS = 255//(X+2)
    NREPORTS = 1333//(X+2)

    t = [i for i in l]
    
    # takes a list with unknown number of elements and returns sublists with 25 or less elements each.
    if values['-IN2-']: # If macros selected
        u = [t[i:i+NMACROS] for i in range(0,len(t),NMACROS)] # stores a list whoes elements are sublists, in 'u'

    # takes a list with unknown number of elements and returns sublists with 25 or less elements each.
    elif values['-IN-']: # If reports selected
        u = [t[i:i+NREPORTS] for i in range(0,len(t),NREPORTS)] # stores a list whoes elements are sublists, in 'u'

    else:
        return 'Please define reports or macros above'


    # takes a list whoes elements are sublists, and prints a string of the elements for each sublist.
    n = 1
    v = []
    for sub in u:
        length = len(sub)
        sub.insert(0, '\n'*2 + '  Argument ' + str(n) + ', Length: ' + str(length) + '\n')
        s = ', '.join(sub)
        v.append(s)
        n += 1
    return ''.join(v)



# GUI

sg.theme('Dark Blue 3')

layout = [[sg.Text('Welcome to the Vehicle Support Center Event Driven Simulation.')],
          [sg.Text('You can paste data from Excel column or any comma-separated list.')],
          [sg.Text('')],
          [sg.Text('Paste the list values here (eg. list of chassis numbers):')],
          [sg.Input(key='-CHASSIS-', size=(720, 12))],
          [sg.Text('Do you want the data sized for macros or reports? Select from the following:')],
          [sg.Radio('Report filters', 'rd1', key='-IN-')],
          [sg.Radio('Macros', 'rd1', key='-IN2-')],
          [sg.Button('Process Data'), sg.Button('Exit')],
          [sg.Text('Output Data:')],
          [sg.Multiline(key='-OUTPUT-', size=(1850, 300))]]

window = sg.Window('VSC Simulation', layout, size=(1280, 720))
reportsText = ['report', 'reports', 'Report', 'Reports', '"reports"']
macrosText = ['macro', 'Macro', 'macros', 'Macros', '"macros"']

while True:  # Event Loop
    event, values = window.read()
    print(event, values)
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Process Data':
        # change the "output" element to be the value of "input" element
        window['-OUTPUT-'].update(makeSubLists(values['-CHASSIS-']))
        

window.close()