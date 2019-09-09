#!/usr/bin/python
import time
import keyboard
import alarm_manager
import json
import os
import gpiozero

# constants
sleep_time = 0.1
use_gpio = True

# Globals
button_pressed = False
alarm_manager_obj = None
configuration = None
button_pin = 18
button = None
check_button_pressed = None

def button_status_gpio():
    return button.is_pressed

def button_status_debug():
    return keyboard.is_pressed('end')

def listen_inputs():
    global button_pressed
    if not button_pressed and check_button_pressed():         
        button_pressed = True
    elif button_pressed and not check_button_pressed():
        button_pressed = False
        alarm_manager_obj.input_action()

def check_runtime():
    if (alarm_manager_obj.check_runtime()):
        data = { "alarmManager": alarm_manager_obj.dump_runtime() }
        with open('runtime.json', 'w') as outfile:      
            json.dump(data,outfile)

def think():
    listen_inputs()

    alarm_manager_obj.think()

    check_runtime()

def write_default_configuration():
    data = {
        "alarmManager": {
            "sources": [
                {
                     "days": [0,1,2,3,4],
                     "hour": "06:30:00",
                     "inhibitors": [{}]                   
                },
                {}
                ],
            "triggers": [
                { "songsPath": "/home/elreveil/songs"},
                {
                    
                },
                {
                    "data":[{},{},{}],
                    "ttsModules": [{},{},{}]
                }
                ]
        },
        "button": {
            "pin": 18
        }
    }
    with open('configuration.json', 'w') as outfile:      
        json.dump(data,outfile)

def get_runtime():
    runtime_default = {
        "alarmManager": {
            "sources": [{"inhibitors": [{}] },{}],
            "triggers": [
                {},
                {                
                },
                {
                    "data":[{},{},{}],
                    "ttsModules": [{},{},{}]
                }
                ]
        }
    }
    if (os.path.exists("runtime.json")):
        try:
            with open('runtime.json') as data:
                return json.load(data)
        except:
            os.remove("runtime.json")
            return runtime_default        
    else:
        return runtime_default

def init():
    global configuration, alarm_manager_obj, button_pin, button, check_button_pressed
    if (not os.path.exists("configuration.json")):
        write_default_configuration()
    with open('configuration.json') as data:
        configuration = json.load(data)
    runtime = get_runtime()
    alarm_manager_obj = alarm_manager.AlarmManager(configuration["alarmManager"], runtime["alarmManager"])
    if not use_gpio:
        check_button_pressed = button_status_debug
    else :
        if "button" in configuration and "pin" in configuration["button"]:
            button_pin = configuration["button"]["pin"]
        button = gpiozero.Button(button_pin)
        check_button_pressed = button_status_gpio

if __name__ == "__main__":
    print("******* el_reveil *******")
    print("Press CTRL+C to break")
    init()
    while True :
        think()
        time.sleep(sleep_time)
