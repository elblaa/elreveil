import os
import glob
import random
import vlc
from time import sleep
from datetime import datetime, time, date, timedelta
import pydub


class SoundTrigger:
    songs_path = None
    songs_selection_type = "AllRandom"
    songs_category = None   
    single_song_path = None
    next_song = None
    selection_type_by_alarm_type = []
    song_object = None
    last_category_fetch = datetime.min
    last_song_updated = datetime.min
    runtime_updated = False
    demo_path = None

    def dump_runtime(self):
        self.runtime_updated = False
        runtime = { 
            "songsCategory": self.songs_category,
            "lastCategoryFetch": self.last_category_fetch.isoformat(),
            "lastSongUpdated": self.last_song_updated.isoformat()
            }
        return runtime

    def check_runtime(self):
        return self.runtime_updated

    def load_runtime(self, runtime):
        if runtime is not None:
            if "songsCategory" in runtime:
                self.songs_category = runtime["songsCategory"]
            if "lastCategoryFetch" in runtime:
                self.last_category_fetch = datetime.fromisoformat(runtime["lastCategoryFetch"])
            if "lastSongUpdated" in runtime:
                self.last_song_updated = datetime.fromisoformat(runtime["lastSongUpdated"])

    def load_configuration(self, configuration, runtime):
        self.songs_path = configuration["songsPath"]
        if "songsSelectionType" in configuration:
            self.songs_selection_type = configuration["songsSelectionType"]
        if "singleSongPath" in configuration:
            self.single_song_path = configuration["singleSongPath"]      
        self.selection_type_by_alarm_type.clear()
        if "selectionTypeByAlarmType" in configuration:
            for alarm_type in configuration["selectionTypeByAlarmType"]:
                selection = SelectionTypeByAlarmType(alarm_type["alarmType"])
                selection.selection_type = alarm_type["selectionType"]
                if "singleSongPath" in alarm_type:
                    selection.single_song_path = alarm_type["singleSongPath"]
                if "songsCategory" in alarm_type:
                    selection.songs_category = alarm_type["songsCategory"]
                self.selection_type_by_alarm_type.append(selection)
        if "demoPath" in configuration:
            self.demo_path = configuration["demoPath"]
        self.load_runtime(runtime)
        # Load after runtime to force value if specified
        if "songsCategory" in configuration:
            self.songs_category = configuration["songsCategory"]

    def __init__(self, configuration, runtime):
        self.load_configuration(configuration, runtime)

    def select_new_song(self, alarm_type):
        selection_type = None
        for selection in self.selection_type_by_alarm_type: 
            if (selection.alarm_type == alarm_type):
                selection_type = selection
                break

        if selection_type is None:
            selection_type = SelectionTypeByAlarmType("default")
            selection_type.selection_type = self.songs_selection_type
            selection_type.single_song_path = self.single_song_path
            selection_type.songs_category = self.songs_category
        
        if (selection_type.selection_type == "SingleSong"):
            self.next_song = self.next_song
        elif (selection_type.selection_type == "CategorySongs" 
        and self.songs_category is not None
        and  os.path.exists(os.path.join(self.songs_path, self.songs_category))):
           self.select_random_song_in_path(os.path.join(self.songs_path, self.songs_category))
        elif (selection_type.selection_type == "RandomCategory"):
            date_difference = (datetime.now() - self.last_category_fetch).days
            if date_difference > 7 or (datetime.today().weekday() == 0 and date_difference >= 1):
                self.select_random_category()
            self.select_random_song_in_path(os.path.join(self.songs_path,self.songs_category))
        else:
            self.select_random_song_in_path(self.songs_path)
        self.song_object = vlc.MediaPlayer(self.next_song)   
        self.last_song_updated = datetime.now()
        print("Next song will be {0}".format(self.next_song))

    def select_random_category(self):
        dirs = next(os.walk(self.songs_path))[1]
        self.songs_category = dirs[random.randrange(len(dirs))]
        print("Song category is now {0}".format(self.songs_category))
        self.last_category_fetch = datetime.now()
        self.runtime_updated = True

    def select_random_song_in_path(self, path):
        songs_in_path = glob.glob(os.path.join(path,"**", "*.mp3"),recursive=True)
        if len(songs_in_path) > 0:
            self.next_song = songs_in_path[random.randrange(len(songs_in_path))]
        else:
            print("There is no songs in {0}".format(path))
            self.next_song = "default.mp3"

    def select_demo_song(self):
        if self.demo_path is None:
            self.demo_path = self.songs_path
        self.select_random_song_in_path(self.demo_path)
        self.song_object = vlc.MediaPlayer(self.next_song)   

    def start_alarm(self, alarm_type):
        if self.next_song is None:            
            self.select_new_song(alarm_type)      
        print("Playing {0}".format(self.next_song))      
        self.song_object.audio_set_volume(100)          
        self.song_object.play()

    def stop_alarm(self):        
        for i in range(20):
            self.song_object.audio_set_volume(100-i*5)            
            sleep(0.1)         
        self.song_object.stop()
        self.song_object = None

    def display_time(self, current_time, next_alarm):
        pass

    def post_alarm(self):
        pass

class SelectionTypeByAlarmType:
    alarm_type = None
    selection_type = None
    single_song_path = None
    songs_category = None

    def __init__(self, alarm_type):
        self.alarm_type = alarm_type