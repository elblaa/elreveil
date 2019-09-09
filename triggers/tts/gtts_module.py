from triggers.tts.tts_module import TTSModule
import gtts
import uuid
import os
import json

class GTTSModule(TTSModule):
    lang = "en"
    name = "gtts"
    can_generate = True
    status = "INIT"
    error_code = None
    tts_path = None
    data = []
    sounds_text = []
    _runtime_updated = False
    enabled = True
    use_file = True

    def load_configuration(self, configuration, runtime):       
        TTSModule.load_configuration(self,configuration,runtime)
        if "lang" in configuration:
            self.lang = configuration["lang"]
            
    def __init__(self, configuration, runtime, tts_path):
        TTSModule.__init__(self,configuration,runtime, tts_path)

    def _generate_data(self, text):       
        try:
            file_name = str(uuid.uuid4())+".mp3"
            tts = gtts.gTTS(text, lang=self.lang)
            tts.save(os.path.join(self.tts_path, file_name))
            entry = {"entry": text, "source": file_name, "start": None, "duration":None}
            self.data.append(entry)
            with open(os.path.join(self.tts_path, "data.json"), 'w') as outfile:      
                json.dump(self.data,outfile)
            self._prepare_data(entry)
            return True
        except gtts.tts.gTTSError:
            self._set_error_code("ERROR_GTTS")
            return False
        



    

    