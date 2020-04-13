from datetime import datetime, time, date, timedelta
from threading import Thread
from time import sleep
import requests
from bs4 import BeautifulSoup
import math
import re
from triggers.data.text_data import TextData

class AirRhoneAlpesData(Thread, TextData):
    name = "Air Rhones-Alpes"
    commune_id = "38185"
    indicator = None
    city = None
    variables_str = [None,None]
    data_str = "Qualité de l'air sur {0} : {1}."
    last_fetch = datetime.min
    nb_error = 0
    status = "INIT"
    error_code = None
    _runtime_updated = False
    enabled = True

    def load_configuration(self, configuration, runtime):
        TextData.load_configuration(self,configuration,runtime)
        if "communeId" in configuration:
            self.meteo_path = configuration["communeId"]
        if "stringData" in configuration:
            self.data_str = configuration["stringData"]

    def __init__(self, configuration, runtime):
        Thread.__init__(self)
        TextData.__init__(self,configuration,runtime)

    def fetch_data(self):  
        self.last_fetch = datetime.now()
        
        self.indicator = None
        self.variables_str[1] = ""
        self.status = "INIT"

        result = None
        try:
            result = requests.get("http://www.air-rhonealpes.fr/monair/commune/"+self.commune_id, timeout=5)   
        except requests.exceptions.Timeout:
            self._set_error_code("GET_DATA_TIMEOUT")
            return        
        
        soup = BeautifulSoup(result.text, 'html.parser') 
        m = re.search("^L'air de ma commune : ([^|]+) |", soup.title.text)  
        self.city = m.group(1)
        self.variables_str[0] = self.city

        indicator = soup.find(id="index-information").div.div.text
        legend_indicator = soup.find_all("li",{"class": "prevision-indice-active"})[0].attrs["data-color"]

        qualification = soup.find_all("div",{"data-color": legend_indicator})[0].text

        self.indicator = "{0}, {1}".format(indicator, qualification)
        self.variables_str[1] = self.indicator

        self.status = "OK"
        if (self.error_code is not None):
            self.error_code = None
            self.runtime_updated = True
        self.nb_error = 0
        print("["+datetime.now().isoformat()+"] Air Rhones-Alpes : "+self.data_str.format(self.city, self.indicator))
        
    def run(self):
        while True:
            difference_fetch = (datetime.now() - self.last_fetch).total_seconds()            
            if (self.status == "ERROR" and difference_fetch > 60 * min(math.pow(2,self.nb_error),1440)):
                self.fetch_data()
            elif (difference_fetch >= 3 * 60 * 60 ):
                self.fetch_data()
            sleep(60)        