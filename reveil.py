#!/usr/bin/python
import time
import keyboard
import alarm_manager
import json
import os
import gpiozero
from datetime import datetime
import vlc

# constants
sleep_time = 0.1
use_gpio = False

# Globals
button_pressed = False
button_pressed_start = None
button_pressed_step_configuration = False
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
    global button_pressed, button_pressed_start, button_pressed_step_configuration
    button_is_pressed = check_button_pressed()
    if not button_pressed and button_is_pressed:    
        button_pressed_start = datetime.now()     
        button_pressed_step_configuration = False   
        button_pressed = True
    elif button_pressed and not button_is_pressed:
        button_pressed = False
        button_pressed_duration = datetime.now() - button_pressed_start
        alarm_manager_obj.input_action(button_pressed_duration)
    elif button_pressed and button_is_pressed and (datetime.now() - button_pressed_start ).total_seconds() >= 2 and not button_pressed_step_configuration:
        button_pressed_step_configuration = True
        media = vlc.MediaPlayer("configuration.wav")   
        media.audio_set_volume(100)
        media.play()
    

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

def init():
    global configuration, alarm_manager_obj, button_pin, button, check_button_pressed
    if (not os.path.exists("configuration.json")):
        write_default_configuration()
    with open('configuration.json') as data:
        configuration = json.load(data)
    alarm_manager_obj = alarm_manager.AlarmManager()
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
