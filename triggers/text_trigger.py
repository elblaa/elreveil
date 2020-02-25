import pyttsx3
from datetime import datetime, time, date, timedelta
from triggers.data import data_meteo, data_air, data_quote
from triggers.tts import pyttsx3_module, gtts_module, custom_module
from threading import Thread
import vlc
import os
import time

class TextTrigger:
    current_time_str = "{0} heures et {1} minutes."
    data_sources = []
    tts_modules = []
    tts_path = None
    is_alarm_in_progress = False
    pending_text = []


    def dump_runtime(self):
        data_sources = []
        for data_source in self.data_sources:
            data_sources.append(data_source.dump_runtime())
        tts_modules = []
        for tts_module in self.tts_modules:
            tts_modules.append(tts_module.dump_runtime())
        return {
            "data": data_sources,
            "ttsModules": tts_modules
        }

    def check_runtime(self):
        for data_source in self.data_sources:
            if data_source.check_runtime():
                return True
        for tts_module in self.tts_modules:
            if tts_module.check_runtime():
                return True
        return False

    def load_configuration(self, configuration, runtime):
        self.tts_path = configuration["ttsPath"]
        if "stringCurrentTime" in configuration:
            self.current_time_str = configuration["stringCurrentTime"]
        for i in range(len(self.data_sources)):
            self.data_sources[i].load_configuration(
                configuration["data"][i], runtime["data"][i])

    def __init__(self, configuration, runtime):
        self.load_configuration(configuration, runtime)
        self.data_sources.append(data_meteo.MeteoFranceData(
            configuration["data"][0], runtime["data"][0]))
        self.data_sources.append(data_air.AirRhoneAlpesData(
            configuration["data"][1], runtime["data"][1]))
        self.data_sources.append(data_quote.WikiQuoteData(
            configuration["data"][2], runtime["data"][2]))
        for data_source in self.data_sources:
            data_source.start()
        self.tts_modules.append(custom_module.CustomModule(
            configuration["ttsModules"][0], runtime["ttsModules"][0], self.tts_path, "elbla"))    
        self.tts_modules.append(gtts_module.GTTSModule(
            configuration["ttsModules"][1], runtime["ttsModules"][1], self.tts_path))
        self.tts_modules.append(pyttsx3_module.PyTTSX3Module(
            configuration["ttsModules"][2], runtime["ttsModules"][2], self.tts_path))
        

    def display_time(self, current_time, next_alarm):
        str_current_time = self.current_time_str.format(
            current_time.hour, current_time.minute, current_time.second)
        current_text_to_process = str_current_time
        self.consume_text(current_text_to_process)
        self.say_text()

    def post_alarm(self):
        self.say_text()

    def start_alarm(self, alarm_type):
        #TODO: Enforce when post alarm before prepare data has ended
        Thread(target=self.prepare_data).start()

    def stop_alarm(self):
        pass

    def say_text(self):
        instance = vlc.Instance()
        current_media_list = None
        media_lists = []
        player = instance.media_list_player_new()
        media_player = player.get_media_player()     
        media_player.audio_set_volume(100)
        for pending in self.pending_text:
            if pending.use_file:
                #TODO: handle file position ?
                if current_media_list is None:
                    current_media_list = instance.media_list_new()
                data_infos = pending.say_text()                
                for data_info in data_infos:
                    media = instance.media_new(os.path.join(pending.tts_path,  data_info["source"]))                   
                    media.get_mrl()
                    current_media_list.add_media(media)                
            else:
                if current_media_list is not None:
                    media_lists.append(current_media_list)
                    current_media_list = None
                media_lists.append(pending)
        if current_media_list is not None:
            media_lists.append(current_media_list)
            current_media_list = None 
        for media in media_lists:
            if type(media) is vlc.MediaList:
                player.set_media_list(media)                          
                player.next()
                state = player.get_state()                
                while state.value != 6:
                    state = player.get_state()
                    time.sleep(0.1)
            else:
                media.say_text()
        self.pending_text.clear()

    def consume_text(self, text):
        remaining = text
        for tts_module in self.tts_modules:
            next_remaining = tts_module.consume_text(remaining)
            if next_remaining != remaining:
                self.pending_text.append(tts_module)
            remaining = next_remaining
            if remaining is None or remaining == "":
                break

    def prepare_data(self):
        errors = []
        for data_source in self.data_sources:
            print("["+datetime.now().isoformat()+"] Get data for module "+data_source.name)
            data_source_text = data_source.get_data()
            if data_source_text is not None:
                self.consume_text(data_source_text)
                print("["+datetime.now().isoformat()+"] data for module "+data_source.name+" has been received")
            elif data_source.status == "ERROR":
                errors.append(" Erreur {0}".format(data_source.name)+".")
            else:
                print("["+datetime.now().isoformat()+"] No data received for module "+data_source.name)
        for error in errors:
            self.consume_text(error)       
