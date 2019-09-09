from triggers.tts.tts_module import TTSModule


class CustomModule(TTSModule):
    name = "Custom"
    can_generate = False
    status = "INIT"
    error_code = None
    tts_path = None
    data = []
    sounds_text = []
    _runtime_updated = False
    enabled = True
    use_file = True

    def __init__(self, configuration, runtime, tts_path, name):
        self.name = name
        TTSModule.__init__(self,configuration,runtime, tts_path)
       