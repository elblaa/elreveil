# El Reveil

This is a simple alarm clock written in python 3.7. This alarm clock has be designed to run on a raspberry pi in combination with speakers, a push button and a RGB led stripe.

This script can run on windows by disabling GPIO (see configuration)

## Features

- Text-to-speech say the current time when the button is pressed or a set of informations after the alarm clock has been stopped
- Reccurrent and temporary alarms
- Songs can be selected by configuration, alarm type, by artist with the artist changing each week, or randomly.
- Music visualization by the RGB leds while the alarm is active
- Configurables modules can retrieve weather, air quality or a quote.
- Demo mode that play songs with led visualization
- Press the button 2 seconds to reload configuration/exit demo mode (a sound is emitted)
- Press the button 6 seconds to enter/exit demo mode (a sound is emitted)

## Installation

Using a raspbian os:

Requirements:
 - vlc
 - espeak

Force sound through jack audio:
`sudo raspi-config` -> Advanced configuration

Modules used:

`pip3 install keyboard python-vlc pydub pyttsx3 gtts`

[How to connect a RGB led stripe to the raspberry](https://dordnung.de/raspberrypi-ledstrip/)

## Configuration

TODO

## Known bugs


## Next features

 - Web server to configure the app
 - Display light after alarm triggered (configurable)
 - TTS initialisation
