from datetime import datetime, time, date, timedelta
from time import sleep

class TextData():
    name = ""
    last_fetch = datetime.min
    nb_error = 0
    status = "INIT"
    error_code = None
    variables_str = []
    data_str = ""
    _runtime_updated = False
    enabled = True

    def dump_runtime(self):
        self._runtime_updated = False
        return { "errorCode": self.error_code }

    def check_runtime(self):
        return self._runtime_updated

    def load_configuration(self, configuration, runtime):
        if "enabled" in configuration:
            self.enabled = configuration["enabled"]

    def __init__(self, configuration, runtime):
        self.load_configuration(configuration, runtime)
        if not self.enabled:
            self.status = "DISABLED"

    def _set_error_code(self, error_code):
        self.status = "ERROR"
        self.error_code = error_code
        self.nb_error += 1
        self._runtime_updated = True
        print("{0} : Error => {1}".format(self.name, error_code))

    def fetch_data(self):          
        pass

    def get_data(self):
        if not self.enabled:
            return None
        start_time = datetime.now()
        while self.status == "INIT" and (datetime.now() - start_time).total_seconds() < 3:
            print("["+datetime.now().isoformat()+"] {0} : waiting data from module {1}".format(self.name, self.data_str))
            sleep(0.1)
        if (self.status == "OK"):
            return self.data_str.format(*self.variables_str)
        else:           
            return None
