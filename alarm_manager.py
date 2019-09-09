from sources import recurrent_alarm, temporary_alarm
from triggers import sound_trigger, text_trigger, light_trigger
from datetime import datetime, time, date, timedelta
import json
import os

class AlarmManager:
    alarm_in_progress = False
    sources = []
    triggers = []
    next_alarm = datetime.min
    next_alarm_type = None
    last_fetch = datetime.min
    last_alert = datetime.min
    runtime_updated = False

    def dump_runtime(self):
        self.runtime_updated = False
        sources = []
        for source in self.sources:
            sources.append(source.dump_runtime())
        triggers = []
        for trigger in self.triggers:
            triggers.append(trigger.dump_runtime())
        return {
            "lastAlert": self.last_alert.isoformat(),
            "sources": sources,
            "triggers": triggers
        }

    def check_runtime(self):
        if self.runtime_updated:
            return True
        for source in self.sources:
            if source.check_runtime():
                return True
        for trigger in self.triggers:
            if trigger.check_runtime():
                return True
        return False

    def load_runtime(self, runtime):
        if runtime is not None:
            if "lastAlert" in runtime:
                self.last_alert = datetime.fromisoformat(runtime["lastAlert"])

    def load_configuration(self, configuration, runtime):
        for i in range(len(self.sources)):
            self.sources[i].load_configuration(
                configuration["sources"][i], runtime["sources"][i])
        for i in range(len(self.triggers)):
            self.triggers[i].load_configuration(
                configuration["triggers"][i], runtime["triggers"][i])

    def get_configuration_files(self):
        with open('configuration.json') as data:
            configuration = json.load(data)
            runtime = self.get_runtime()
            return (configuration, runtime)

    def get_runtime(self):
        runtime_default = {
            "alarmManager": {
                "sources": [{"inhibitors": [{}] },{}],
                "triggers": [
                    {},
                    {                
                    },
                    {
                        "data":[{},{},{}],
                        "ttsModules": [{},{},{}]
                    }
                    ]
            }
        }
        if (os.path.exists("runtime.json")):
            try:
                with open('runtime.json') as data:
                    return json.load(data)
            except:
                os.remove("runtime.json")
                return runtime_default        
        else:
            return runtime_default        

    def __init__(self):        
        files = self.get_configuration_files()
        configuration = files[0]["alarmManager"]
        runtime = files[1]["alarmManager"]
        self.sources.append(recurrent_alarm.RecurrentAlarm(
            configuration["sources"][0], runtime["sources"][0]))
        self.sources.append(temporary_alarm.TemporaryAlarm(
            configuration["sources"][1], runtime["sources"][1]))
        self.triggers.append(sound_trigger.SoundTrigger(
            configuration["triggers"][0], runtime["triggers"][0]))
        light_trg = light_trigger.LightTrigger(configuration["triggers"][1], runtime["triggers"][1], self.triggers[0])
        self.triggers.append(light_trg)
        self.triggers.append(text_trigger.TextTrigger(
            configuration["triggers"][2], runtime["triggers"][2]))
                
        self.load_runtime(runtime)
        light_trg.start()

    def update_next_alarm(self):
        self.next_alarm = datetime.min
        self.last_fetch = datetime.now()
        for source in self.sources:
            next_alarm_candidate = source.next_alarm(self.last_alert)
            if next_alarm_candidate is not None and (self.next_alarm == datetime.min or next_alarm_candidate < self.next_alarm):
                self.next_alarm = next_alarm_candidate
                self.next_alarm_type = source.alarm_type
        print("Next alarm is {0}".format(self.next_alarm.isoformat()))
        self.triggers[0].select_new_song(self.next_alarm_type)
        self.runtime_updated = True

    def trigger_alert(self):
        print("Alarm triggered")
        self.last_alert = datetime.now()
        self.alarm_in_progress = True
        for trigger in self.triggers:
            trigger.start_alarm(self.next_alarm_type)
        self.runtime_updated = True

    def think(self):
        if self.last_fetch.date() < date.today():
            self.update_next_alarm()

        time_difference = (datetime.now() - self.next_alarm).total_seconds()

        if(self.last_alert < self.next_alarm
                and time_difference >= 0
                and time_difference < 3 * 60 * 60):
            self.trigger_alert()

    def input_action(self, input_duration):
        if (self.alarm_in_progress):
            self.alarm_in_progress = False
            print("Alarm stopped")
            for trigger in self.triggers:
                trigger.stop_alarm()
            for trigger in self.triggers:
                trigger.post_alarm()
            self.update_next_alarm()
        elif input_duration.total_seconds() >= 2:
            print("Reload configuration...")
            files = self.get_configuration_files()
            self.load_configuration(files[0]["alarmManager"], files[1]["alarmManager"])
            self.update_next_alarm()
        else:
            for trigger in self.triggers:
                trigger.display_time(datetime.now(), self.next_alarm)
