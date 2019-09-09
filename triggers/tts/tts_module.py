import os
from pydub import AudioSegment
from pydub.playback import play
import json
import vlc
import time

class TTSModule():
    name = "default"
    can_generate = False
    status = "INIT"
    error_code = None
    tts_path = None
    data = []
    sounds_text = []
    _runtime_updated = False
    enabled = True
    use_file = True

    def dump_runtime(self):
        self._runtime_updated = False
        return { "errorCode": self.error_code }

    def check_runtime(self):
        return self._runtime_updated
    
    def load_configuration(self, configuration, runtime):
        if "canGenerate" in configuration:
             self.can_generate = configuration["canGenerate"]
        if "enabled" in configuration:
            self.enabled = configuration["enabled"]

    def __init__(self, configuration, runtime, tts_path):
        self.load_configuration(configuration, runtime)
        self.tts_path = os.path.join(tts_path, self.name)
        self._load_data()
    
    def _load_data(self):
        if not self.enabled:
            return
        try:
            with open(os.path.join(self.tts_path, "data.json")) as data:
                self.data = json.load(data)
        except:
            self._set_error_code("ERROR_LOAD_DATA")

    def _set_error_code(self, error_code):
        self.status = "ERROR"
        self.error_code = error_code
        self._runtime_updated = True
        print("{0} : Error => {1}".format(self.name, error_code))

    def _generate_data(self, text):
        return False

    def _prepare_data(self,data):
        self.sounds_text.append(data)
    
    def consume_text(self, text):
        if not self.enabled:
            return text
        if text is None or text == "":
            return None
        matching_data = {}
        text_stripped = text.strip()
        for entry in self.data:
            if text_stripped.startswith(entry["entry"]) and (matching_data == {} or len(entry["entry"]) > len(matching_data["entry"])):
                matching_data = entry
                if (matching_data["entry"] == text_stripped):
                    break
        if matching_data == {}:
            if self.can_generate and self._generate_data(text):                
                return None
            else:
                return text
        else:
            self._prepare_data(matching_data)
            if matching_data["entry"] == text_stripped:
                return None
            else:            
                text_remaining  = text_stripped[len(matching_data["entry"]):]
                return self.consume_text(text_remaining)

    def say_text(self):
        if self.enabled and self.sounds_text is not None:
            temp = self.sounds_text.copy()
            self.sounds_text.clear()
            return temp