from datetime import datetime, time, date, timedelta
from threading import Thread
from time import sleep
import requests
from bs4 import BeautifulSoup
import math
from triggers.data.text_data import TextData

class MeteoFranceData(Thread, TextData):
    name = "Météo France"    
    meteo_path = "/grenoble/38000"    
    min_temp = None
    max_temp = None
    weather = None
    variables_str = [None,None,None]
    data_str = "Météo : {0}, {1}, temps : {2}."

    last_fetch = datetime.min
    nb_error = 0
    status = "INIT"
    error_code = None
    _runtime_updated = False
    enabled = True

    def load_configuration(self, configuration, runtime):
        super(MeteoFranceData, self).load_configuration(configuration,runtime)
        if "meteoPath" in configuration:
            self.meteo_path = configuration["meteoPath"]
        if "stringData" in configuration:
            self.data_str = configuration["stringData"]

    def __init__(self, configuration, runtime):
        Thread.__init__(self)
        TextData.__init__(self,configuration,runtime)

    def fetch_data(self):  
        if not self.enabled:
            return
        self.last_fetch = datetime.now()

        result = None
        try:
            result = requests.get("http://www.meteofrance.com/previsions-meteo-france"+self.meteo_path, timeout=5)        
        except requests.exceptions.Timeout:
            self._set_error_code("GET_DATA_TIMEOUT")
            return     

        soup = BeautifulSoup(result.text, 'html.parser')        
        liste_jours =  soup.findAll("div",{"class": "liste-jours"})
        if liste_jours is None or len(liste_jours) == 0:
            self._set_error_code("LISTE_JOURS_NOT_FOUND")
            return
        
        active = liste_jours[0].findAll("li",{"class": "active"})
        if active is None or len(active) == 0:
            self._set_error_code("ACTIVE_NOT_FOUND")
            return

        min_temperature = active[0].findAll("span",{"class": "min-temp"})
        if min_temperature is None or len(min_temperature) == 0:
            self._set_error_code("MIN_TEMPERATURE_NOT_FOUND")
            return

        max_temperature = active[0].findAll("span",{"class": "max-temp"})
        if max_temperature is None or len(max_temperature) == 0:
            self._set_error_code("MAX_TEMPERATURE_NOT_FOUND")
            return

        self.min_temp = min_temperature[0].text
        self.max_temp = max_temperature[0].text
        self.weather = active[0].attrs["title"]
        self.variables_str[0] = self.min_temp
        self.variables_str[1] = self.max_temp
        self.variables_str[2] = self.weather
        self.status = "OK"
        if (self.error_code is not None):
            self.error_code = None
            self.runtime_updated = True
        self.nb_error = 0
        print("Meteo france : "+self.data_str.format(self.min_temp, self.max_temp, self.weather))
        
    def run(self):
        while True:
            difference_fetch = (datetime.now() - self.last_fetch).total_seconds()            
            if (self.status == "ERROR" and difference_fetch > 60 * min(math.pow(2,self.nb_error),1440)):
                self.fetch_data()
            elif (difference_fetch >= 3 * 60 * 60 ):
                self.fetch_data()
            sleep(60)        