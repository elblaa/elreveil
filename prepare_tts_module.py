import pyttsx3
import re
import os
import sys
import pydub
import json
import gtts
import uuid

tts_path = "tts_data"
date_format = "{0} heures |et {1} minutes."
name = "elbla"

configuration = {"voice": None}

def generate_date(text, path):
    tts = gtts.gTTS(text, lang="fr")
    tts.save(path)

if __name__ == "__main__":
    split = ["{0} heures ","et {1} minutes."]
    str_dates = ""
    data = []

    for k in range(24):
        str_dates = ""
        file_name = "{0}h.mp3".format(k) #str(uuid.uuid4())+".mp3"
        if k == 0:
            str_dates += "Minuit "
        else:
            str_dates += ", "+split[0].format(k)
        #tts = gtts.gTTS(str_dates, lang="fr")
        #tts.save(os.path.join(tts_path,name, file_name))
        entry = { "entry": split[0].format(k), "source":file_name, "start": None, "duration": None }
        data.append(entry)
    for k in range(60):
        str_dates = ""
        file_name = "{0}m.mp3".format(k)#str(uuid.uuid4())+".mp3"
        if k == 0:
            str_dates += " pile."
        elif k == 15:
            str_dates += " et quart."
        elif k == 30:
            str_dates += " et demi."
        else:
            str_dates += ", "+split[1].format(0,k)
        #tts = gtts.gTTS(str_dates, lang="fr")
        #tts.save(os.path.join(tts_path,name, file_name))
        entry = { "entry": split[1].format(0,k), "source":file_name, "start": None, "duration": None }
        data.append(entry)

    if os.path.exists(os.path.join(tts_path, name)):
        print("A module named {0} already exist".format(name))
        #sys.exit(0)
    else:
        os.mkdir(os.path.join(tts_path, name))

    destination_data = os.path.join(tts_path,name,"data.json")
    destination_data = os.path.join(tts_path,name,"data_backup.json")
    destination_to_synthesize = os.path.join(tts_path,name,"to_say.txt")
    destination_dates = os.path.join(tts_path,name,"dates.mp3")
    #engine = pyttsx3.init()
    generate_date(str_dates, destination_dates)


    with open(destination_data, 'w') as outfile:      
        json.dump(data,outfile)

    with open(destination_to_synthesize, 'w') as outfile:      
        outfile.write(str_dates)




