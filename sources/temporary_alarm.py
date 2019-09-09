from datetime import datetime, time, date, timedelta

class TemporaryAlarm:
    next_dates = []
    alarm_type = "Temporary"

    def dump_runtime(self):
        return {}

    def check_runtime(self):
        return False

    def load_configuration(self, configuration, runtime):
        if "dates" in configuration:
            dates = []
            for date in configuration["dates"]:
                date_candidate = datetime.fromisoformat(date)
                if (date_candidate >= datetime.now() + timedelta(0,-15*60)):
                    dates.append(date_candidate)
            self.next_dates = sorted(dates)

    def __init__(self, configuration, runtime):
        self.load_configuration(configuration, runtime) 

    def next_alarm(self, last_alarm):
        if len(self.next_dates) > 0:
            dates = sorted(self.next_dates)
            for date in dates:
                if (date > last_alarm):
                    return date
        return None