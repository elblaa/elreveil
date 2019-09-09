from datetime import datetime, time, date, timedelta
from threading import Thread
from time import sleep
import requests
import random
import math
from bs4 import BeautifulSoup
from triggers.data.text_data import TextData

class WikiQuoteData(Thread, TextData):
    name = "WikiQuote"
    wikiquote_url = "https://fr.wikiquote.org"
    categories = ["Président de la République française", "Personnalité politique française"]
    author = None
    category = None
    quote = None
    variables_str = [None,None,None]
    data_str = "Citation de {0} - {1} : {2}."
    quote_max_length = 350

    last_fetch = datetime.min
    nb_error = 0
    status = "INIT"
    error_code = None
    _runtime_updated = False
    enabled = True

    def load_configuration(self, configuration, runtime):
        TextData.load_configuration(self,configuration,runtime)
        if "categories" in configuration:
            self.categories = configuration["categories"]
        if "wikiQuoteUrl" in configuration:
            self.wikiquote_url = configuration["wikiQuoteUrl"]
        if "stringData" in configuration:
            self.data_str = configuration["stringData"]
        if "quoteMaxLength" in configuration:
            self.quote_max_length = configuration["quoteMaxLength"]

    def __init__(self, configuration, runtime):
        Thread.__init__(self)
        TextData.__init__(self,configuration,runtime)

    def fetch_data(self): 
        previous_fetch = self.last_fetch 
        self.last_fetch = datetime.now()

        self.category = self.categories[random.randrange(len(self.categories))]
        self.variables_str[1] = self.category
        category = "Catégorie:"+self.category

        page = None
        try:
            resultPages = requests.get(self.wikiquote_url+"/w/api.php?action=query&format=json&prop=info&generator=categorymembers&gcmtitle="+category+"&gcmlimit=max", timeout=5) 
            titles = list(resultPages.json()["query"]["pages"].values())
            page = titles[random.randrange(len(titles))]
        except requests.exceptions.Timeout:
            self._set_error_code("ERROR_GET_DATA_CATEGORIES")
        except:
            self._set_error_code("ERROR_CATEGORY")
            return
        section = None
        try:
            resultsPage = requests.get(self.wikiquote_url+"/w/api.php?action=parse&format=json&pageid="+str(page["pageid"])+"&prop=sections", timeout=5).json()
            self.author = resultsPage["parse"]["title"]
            self.variables_str[0] = self.author
            sections = [x for x in resultsPage["parse"]["sections"] if not "citations sur" in x["line"].lower()]
            if (len(sections) == 0):
                print("Wikiquote: No sections for {0} ({1})".format(self.author, page["pageid"]))
                self.last_fetch = previous_fetch
                return 
            section = sections[random.randrange(len(sections))]
        except requests.exceptions.Timeout:
            self._set_error_code("ERROR_GET_DATA_SECTIONS")
        except:
            self._set_error_code("ERROR_SECTION")
            return
        try:
            quotes = requests.get(self.wikiquote_url+"/w/api.php?action=parse&format=json&pageid="+str(page["pageid"])+"&section="+str(section["index"])+"&noimages=1", timeout=5).json()
            soup = BeautifulSoup(quotes["parse"]["text"]["*"], 'html.parser')
            quotes_text = soup.find_all("div",{"class": "citation"})
            quotes_text_restricted =  [x for x in quotes_text if len(x.text) <= self.quote_max_length and len(x.text) > 0]
            if len(quotes_text_restricted) == 0:
                print("Wikiquote: No valid quotes for {0} ({1}) - [{2}]".format(self.author, page["pageid"], section["index"]))
                self.last_fetch = previous_fetch
                return

            self.quote = quotes_text_restricted[random.randrange(len(quotes_text_restricted))].text.replace("&#160;","")
            self.variables_str[2] = self.quote
        except requests.exceptions.Timeout:
            self._set_error_code("ERROR_GET_DATA_QUOTES")
        except:
            self._set_error_code("ERROR_QUOTE")
            return

        self.status = "OK"
        if (self.error_code is not None):
            self.error_code = None
            self.runtime_updated = True
        self.nb_error = 0
        print("Wikiquote : "+self.data_str.format(self.author, self.category, self.quote))
        
    def run(self):
        while True:
            difference_fetch = (datetime.now() - self.last_fetch).total_seconds()     
            if (self.status == "ERROR" and difference_fetch > 60 * min(math.pow(2,self.nb_error),1440)):
                self.fetch_data()
            elif (difference_fetch >= 24 * 60 * 60 ):
                self.fetch_data()
            sleep(1)        
