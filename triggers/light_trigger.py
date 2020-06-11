from datetime import datetime, time, date, timedelta
from threading import Thread
from time import sleep
import random
import gpiozero
import colorsys
import numpy
import os
import pydub
import pickle
import json

class LightTrigger(Thread):
    sound_trigger = None
    alarm_in_progress = False
    enabled = True
    time_displayed = None
    next_alarm = None
    time_fading_transition = 1000
    time_transition = 3000
    pin_id_red = 27
    pin_id_green = 23
    pin_id_blue = 25
    gpio_red = None
    gpio_green = None
    gpio_blue = None
    processing_light_data = False

    display_light = False
    displayed_light_hue = 0
    displayed_light_hue_change_interval = 10 #time in second after next hue is displayed
    displayed_light_hue_current_interval = 1

    light_data = "light_data"
    time_range = 0.05
    pitch_color_max = 360
    freq_start = 1760 # start of frequencies used with fft (start of equal temperament)
    freq_end = 3520 # end of frequencies used with fft (end of equal temperament)
    peak_factor = 5
    fft_thresold = 1
    saturation = 0.95
    peak_value = 0.95
    song_data = []
    song_loaded = None
    frame_rate = 44100

    def dump_runtime(self):
        return {}

    def check_runtime(self):
        return False

    def load_runtime(self, runtime):
        pass

    def load_configuration(self, configuration, runtime):
        if "lightData" in configuration:
            self.light_data = configuration["lightData"]
        if not os.path.exists(self.light_data):
            os.mkdir(self.light_data)
        if "enabled" in configuration:
            self.enabled = configuration["enabled"]
        if "timeTransition" in configuration:
            self.time_transition = configuration["timeTransition"]
        if "timeFadingTransition" in configuration:
            self.time_fading_transition = configuration["timeFadingTransition"]
        if "pinRed" in configuration:
            self.pin_id_red = configuration["pinRed"]
        if "pinGreen" in configuration:
            self.pin_id_green = configuration["pinGreen"]
        if "pinBlue" in configuration:
            self.pin_id_blue = configuration["pinBlue"]
        if "timeRange" in configuration:
            self.time_range = configuration["timeRange"]
        if "pitchColorMax" in configuration:
            self.pitch_color_max = configuration["pitchColorMax"]
        if "frequencyStart" in configuration:
            self.freq_start = configuration["frequencyStart"]
        if "frequencyEnd" in configuration:
            self.freq_end = configuration["frequencyEnd"]
        if "peakFactor" in configuration:
            self.peak_factor = configuration["peakFactor"]
        if "fftThresold" in configuration:
            self.fft_thresold = configuration["fftThresold"]
        if "saturation" in configuration:
            self.saturation = configuration["saturation"]
        if "peakValue" in configuration:
            self.peak_value = configuration["peakValue"]
        if "displayedLightHueChangeInterval" in configuration:
            self.displayed_light_hue_change_interval = configuration["displayedLightHueChangeInterval"]
        
        self.load_runtime(runtime)

    def __init__(self, configuration, runtime, sound_trigger):
        Thread.__init__(self)
        self.sound_trigger = sound_trigger
        self.load_configuration(configuration, runtime)
        if self.enabled:
            self._init_led()

    def _init_led(self):
        self.gpio_red = gpiozero.PWMLED(self.pin_id_red)
        self.gpio_green = gpiozero.PWMLED(self.pin_id_green)
        self.gpio_blue = gpiozero.PWMLED(self.pin_id_blue)
        self._put_color(0,0,0)     

    def _put_color_hsv(self, hue, saturation, peak):
        rgb_color = colorsys.hsv_to_rgb(hue/360, saturation, peak)
        self._put_color(rgb_color[0],rgb_color[1],rgb_color[2])

    def get_proper_gpio_color_value(self, value):
        if value > 0.001:
            return max(0,min(1,value))
        return 0

    def _put_color(self, red, green, blue):
        self.gpio_red.value = self.get_proper_gpio_color_value(red)
        self.gpio_green.value = self.get_proper_gpio_color_value(green)
        self.gpio_blue.value = self.get_proper_gpio_color_value(blue)

    def start_alarm(self, alarm_type):
        self.alarm_in_progress = True

    def stop_alarm(self):
        self.alarm_in_progress = False

    def _transition_to_color(self, hue_start, saturation_start, peak_start, hue_end, saturation_end, peak_end):
        number_of_transition_interval = int(self.time_fading_transition / 50)
        hue_value_interval = abs(hue_end - hue_start) / number_of_transition_interval
        saturation_interval = (saturation_end - saturation_start) / number_of_transition_interval
        peak_interval = (peak_end - peak_start) / number_of_transition_interval
        for i in range(number_of_transition_interval): 
            rgb_color = colorsys.hsv_to_rgb((hue_start + i * hue_value_interval) % 360/ 360, saturation_start + i * saturation_interval, peak_start + i * peak_interval)
            self._put_color(rgb_color[0],rgb_color[1],rgb_color[2])
            sleep(0.05)
        self._put_color_hsv(hue_end, saturation_end, peak_end)

    def display_time(self, current_time, next_alarm):
        self.time_displayed = current_time
        self.next_alarm = next_alarm

    def _display_time(self):
        if self.next_alarm is None:
            self.next_alarm = datetime.today()
        # Blue when alarm is < 8 hr then start to shift to red using f(x) = x^2 * 3.6
        hue = min(240,  (abs(self.next_alarm - self.time_displayed) / timedelta(hours=1))**2 * 3.6)       

        hue_start = hue
        saturation_start = self.saturation
        peak_start = 0
        if self.display_light:
            hue_start =  self.displayed_light_hue
            peak_start = self.peak_value
        self._transition_to_color(hue_start, saturation_start, peak_start, hue, self.saturation, self.peak_value)

        self._put_color_hsv(hue,self.saturation,self.peak_value)
        sleep(self.time_transition / 1000)

        hue_end = hue
        saturation_end = self.saturation
        peak_end = 0
        if self.display_light: 
            hue_end = self.displayed_light_hue
            peak_end = self.peak_value

        self._transition_to_color(hue, self.saturation, self.peak_value, hue_end, saturation_end, peak_end)       
        
        if not self.display_light:
            self._put_color(0,0,0)
        self.time_displayed = None

    def post_alarm(self):
        pass

    def _loop_alarm(self):
        start_vlc = timedelta()
        start_date = datetime.now()

        song_object = self.sound_trigger.song_object
        fftsize = int(self.frame_rate * self.time_range)
        color = 0
        saturation = 0
        peak = 0

        #display song data
        while self.alarm_in_progress:    
            if len(self.song_data) == 0:
                continue
            if (start_vlc == timedelta()):
                vlc_duration = song_object.get_time()
                current_time = datetime.now()
                if vlc_duration != -1:
                    start_vlc = current_time - start_date - timedelta(milliseconds=vlc_duration)
                    print("time_vlc is {0}".format(start_vlc))
                else:
                    continue
            time_fetch = datetime.now() - start_date + start_vlc   
            index = int(time_fetch.total_seconds() * (self.frame_rate / fftsize))
            sample = self.song_data[min(index, len(self.song_data) - 1)]
            saturation = sample[1]
            peak = sample[0]
            color = sample[2]
            rgb_color =  colorsys.hsv_to_rgb(color,saturation, peak)
            self._put_color(rgb_color[0],rgb_color[1],rgb_color[2])
            sleep(self.time_range)   

        #end transition            
        if not self.display_light:
            self._transition_to_color(color, saturation, peak, color, saturation, 0)   
            self._put_color(0,0,0)
        else:
            self._transition_to_color(color, saturation, peak, self.displayed_light_hue, self.saturation, self.peak_value)
    
    def _prepare_song_data(self):
        if self.sound_trigger.next_song is None:
            return
        elif self.song_loaded == self.sound_trigger.next_song:
            return
        self.processing_light_data = True
        file_data_path = os.path.join(self.light_data, os.path.basename(self.sound_trigger.next_song)+".lightdata")
        file_info_data_path = os.path.join(self.light_data, os.path.basename(self.sound_trigger.next_song)+".json")
        if os.path.exists(file_data_path):
            with open(file_data_path,"rb") as fd:
                self.song_data = pickle.load(fd)
            with open(file_info_data_path) as data:
                self.frame_rate = json.load(data)["frameRate"]
            self.song_loaded = self.sound_trigger.next_song
            self.processing_light_data = False
        else:
            start_date = datetime.now()
            print("Getting light data from {0}...".format(self.sound_trigger.next_song))
            song_object = pydub.AudioSegment.from_mp3(self.sound_trigger.next_song)
            song_samples = song_object.get_array_of_samples()
            song_data = numpy.asarray(song_samples) #convert to numpy array
            if song_object.channels > 1:
                song_data = numpy.reshape(song_data,(-1,song_object.channels)) #make it stereo
            fftsize = int(song_object.frame_rate * self.time_range)
            number = len(song_data) / fftsize
            song_data_sampled = numpy.array_split(song_data,  number)
            self.song_data = []
            maximum = song_object.max
            hue_offset = sum(map(ord,self.sound_trigger.next_song))
 
            frequencies= numpy.fft.rfftfreq(fftsize,d = 1./song_object.frame_rate)
            index_start_freq = numpy.searchsorted(frequencies, self.freq_start)
            if index_start_freq > 0 and frequencies[index_start_freq] > self.freq_start:
                index_start_freq -= 1
            index_end_freq = numpy.searchsorted(frequencies,self.freq_end, side='right')
            if index_end_freq < len(frequencies) and frequencies[index_start_freq] < self.freq_start:
                index_end_freq += 1

            pitch = [27.500,29.135,30.868,32.703,34.648,36.708,38.891,41.204,43.654,46.249,48.999,51.913] #Equal temperament : https://www.dolmetsch.com/musictheory27.htm

            pitch_color_interval = float(self.pitch_color_max)/len(pitch)
            pitch_color = numpy.append(numpy.arange(0,self.pitch_color_max,pitch_color_interval), self.pitch_color_max)            
            hue = hue_offset % 360 / 360

            for sample in song_data_sampled:
                #saturation = numpy.mean(numpy.abs(sample)) / maximum
                saturation = self.saturation              
                peak =  numpy.mean(numpy.ptp(numpy.abs(sample), axis=0)) / maximum
                if self.peak_factor > 1:
                    #peak = pow(peak,1/((self.peak_factor ** 2)*pow(peak,self.peak_factor)))
                    peak = pow(peak,1/(self.peak_factor * peak)+ 0.6)
                
                fft = numpy.abs(numpy.real(numpy.fft.rfft(sample))) 
                current_max = numpy.amax(fft[index_start_freq:index_end_freq])
                
                if current_max >= self.fft_thresold* maximum:
                    index = numpy.where(fft == current_max)[0][0]
                    max_fft_freq = frequencies[index_start_freq + index % len(frequencies)]  
                    index_pitch = 0
                    num_octave = 1
                    while max_fft_freq > pitch[index_pitch] * 2 ** num_octave:
                        index_pitch += 1
                        if index_pitch >= len(pitch):
                            index_pitch = 0
                            num_octave += 1
                    hue = (hue_offset + pitch_color[index_pitch]  ) % 360  / 360      
        
                peak = max(0,min(1, peak))
                #saturation = max(0,min(1, 0.7 + saturation))
                self.song_data.append([peak, saturation, hue])

            with open(file_data_path,"wb") as fd:
                pickle.dump(self.song_data,fd)
            with open(file_info_data_path, 'w') as outfile:      
                json.dump({"frameRate": song_object.frame_rate},outfile)
            self.song_loaded = self.sound_trigger.next_song     
            self.processing_light_data = False
            print("Light data for {0} written in {1} seconds".format(self.sound_trigger.next_song, (datetime.now() - start_date).total_seconds()))   

    def toggle_light(self):
        if self.enabled:
            self.display_light =  not self.display_light        
            if self.display_light:
                self.displayed_light_hue = random.randint(0,360)
                self._transition_to_color(self.displayed_light_hue,self.saturation,0,self.displayed_light_hue, self.saturation, self.peak_value)
            else:
                self._transition_to_color(self.displayed_light_hue,self.saturation,self.peak_value,self.displayed_light_hue, self.saturation, 0)    
            print("Toggle light : {0} - {1}".format(self.display_light, self.displayed_light_hue))

    def manage_light(self):
        if self.display_light:
            if self.displayed_light_hue_current_interval % (self.displayed_light_hue_change_interval * 10) == 0:
                self.displayed_light_hue = (self.displayed_light_hue + 1) % 360
                self.displayed_light_hue_current_interval = 0
                self._put_color_hsv(self.displayed_light_hue, self.saturation, self.peak_value)
            self.displayed_light_hue_current_interval += 1

    def run(self):
        while self.enabled:
            if self.time_displayed is not None:
                self._display_time()                
            elif self.alarm_in_progress:
                self._loop_alarm()
            else:
                self.manage_light()
                self._prepare_song_data()
            sleep(0.1)