from datetime import datetime, time, date, timedelta
from threading import Thread
from time import sleep
import requests
import math
from bs4 import BeautifulSoup
import base64
import json


class ShivaInhibitor(Thread):
    name = "Shiva Viseo"
    last_fetch = datetime.min
    nb_error = 0
    status = "INIT"
    error_code = None
    _runtime_updated = False
    user_name = None
    password = None
    planning = {}
    url = "https://shiva.viseo.net"

    def dump_runtime(self):
        self._runtime_updated = False
        return {"errorCode": self.error_code}

    def check_runtime(self):
        return self._runtime_updated

    def load_configuration(self, configuration, runtime):
        if "userName" in configuration:
            self.user_name = configuration["userName"]
        if "password" in configuration:
            self.password = configuration["password"]
        if "url" in configuration:
            self.url = configuration["url"]

    def __init__(self, configuration, runtime):
        Thread.__init__(self)
        self.load_configuration(configuration, runtime)

    def _set_error_code(self, error_code):
        self.status = "ERROR"
        self.error_code = error_code
        self.nb_error += 1
        self._runtime_updated = True
        print("{0} : Error => {1}".format(self.name, error_code))

    def fetch_data(self):
        self.last_fetch = datetime.now()
        self.planning.clear()

        if self.user_name is None or self.password is None:
            self.status = "NO_CREDENTIALS"
            if (self.status != "NO_CREDENTIALS"):
                self._runtime_updated = True
            return

        session = requests.session()
        
        csrf_token = None
        login = None
        try:
            login = session.get(self.url+"/login", timeout=5)
        except requests.exceptions.Timeout:
            self._set_error_code("ERROR_TIMEOUT_GET_LOGIN_PAGE")  
            return      
        if (login.status_code != 200):
            self._set_error_code("ERROR_GET_LOGIN_PAGE")
            return
        soup = BeautifulSoup(login.text, 'html.parser')
        csrf_inputs = soup.findAll("input", {"name": "_csrf_token"})
        if csrf_inputs is None or len(csrf_inputs) == 0:
            self._set_error_code("ERROR_GET_CSRF_LOGIN_PAGE")
            return
        csrf_token = csrf_inputs[0].attrs["value"]

        password_d = base64.b64decode(self.password).decode()
        credentials = {
            "_username": self.user_name,
            "_password": password_d,
            "_remember_me": "on",
            "_csrf_token": csrf_token
        }
        login_check = None
        try:
            login_check = session.post(self.url+"/login_check", data=credentials)
        except requests.exceptions.Timeout:
            self._set_error_code("ERROR_TIMEOUT_LOGIN_CHECK")  
            return       
        if login_check.status_code != 200:
            self._set_error_code("LOGIN_CHECK_FAILED")
            return

        vacations = None
        try:           
            vacations = session.get(self.url + "/conges/user/list")
        except requests.exceptions.Timeout:
            self._set_error_code("ERROR_TIMEOUT_VACATION")  
            return       

        soup = BeautifulSoup(vacations.text, 'html.parser')
        csrf_inputs = soup.findAll("input", {"name": "_csrf_token"})
        if csrf_inputs and len(csrf_inputs) > 0:
            self._set_error_code("ERROR_LOGIN_VACATION")
            return        

        try:
            script_content = soup.findAll("script")[23].text
            start_script_demand = "var loaded_demandes  = "
            loaded_demands_start = script_content.index(start_script_demand) + len(start_script_demand)
            loaded_demands_stop = script_content.index(";", loaded_demands_start  )
            loaded_demands = json.loads(script_content[loaded_demands_start:loaded_demands_stop])

            for demand in loaded_demands:
                if demand["etat"] == 1 or demand["etat"] == 2:
                    prefix_id = "type_conge_"+str(demand["type_conge_id"])
                    for td_id in demand["td_ids"]:
                        self.planning[td_id[len(prefix_id)+1:]] = True

            #Add non working days
            lines = soup.findAll("tr", {"class": "type_conge_1"})
            now = datetime.now()
            if lines is not None:
                columns = lines[0].findAll("td")
                current_day = 1
                for column in columns:
                    if "class" in column.attrs and "non_worked_day" in column.attrs["class"]:
                        self.planning["{0}-{1:0=2d}-{2:0=2d}_morning".format(
                            now.year, now.month, int(current_day))] = True
                        self.planning["{0}-{1:0=2d}-{2:0=2d}_afternoon".format(
                            now.year, now.month, int(current_day))] = True
                        current_day += 1  
                    elif "id" in column.attrs:
                        current_day += 0.5
        except:
            self._set_error_code("ERROR_PARSING_VACATION")
            return

        self.status = "OK"
        if (self.error_code is not None):
            self.error_code = None
            self._runtime_updated = True
        self.nb_error = 0

    def is_next_date_valid(self, next_date):
        #Wait for shhiva to be fetch
        start_time = datetime.now()
        while self.status == "INIT" and (datetime.now() - start_time).total_seconds() < 25:
            sleep(0.5)

        date_thresold = datetime(next_date.year, next_date.month, next_date.day, 12,0,0)
        qualifier = "morning"
        if next_date >= date_thresold:
            qualifier = "afternoon"       
        return not "{0}-{1:0=2d}-{2:0=2d}_{3}".format(next_date.year, next_date.month, next_date.day, qualifier) in self.planning

    def run(self):
        while True:
            difference_fetch = (
                datetime.now() - self.last_fetch).total_seconds()
            if (self.status == "ERROR" and difference_fetch > 60 * min(math.pow(2, self.nb_error), 1440)):
                self.fetch_data()
            elif (datetime.today().date() > self.last_fetch.date()):
                self.fetch_data()
            sleep(60)
