from triggers.tts.tts_module import TTSModule
import pyttsx3

class PyTTSX3Module(TTSModule):
    engine = pyttsx3.init()
    voice = None
    can_generate = True
    status = "INIT"
    error_code = None
    tts_path = None
    data = []
    sounds_text = []
    _runtime_updated = False
    enabled = True
    use_file = False

    def load_configuration(self, configuration, runtime):       
        super(PyTTSX3Module, self).load_configuration(configuration,runtime)
        if "voice" in configuration:
            self.voice = None
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if voice.name == configuration["voice"]:
                    self.voice = voice
                    break
            if self.voice is None:
                self.engine.setProperty("voice",voices[0].id)
            else:
                self.engine.setProperty("voice",self.voice.id)

    def _generate_data(self, text):
        self.consume_text(text)

    def consume_text(self, text):
        if self.enabled:
            self.sounds_text.insert(0,text)

    def say_text(self):
        if self.enabled and len(self.sounds_text) > 0:
            text = self.sounds_text.pop()
            self.engine.say(text)
            self.engine.runAndWait()