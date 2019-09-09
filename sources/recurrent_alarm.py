from datetime import datetime, time, date, timedelta
from sources import shiva_inhibitor

class RecurrentAlarm:
    days = [0,1,2,3,4]
    hour = time(hour=6, minute=30, second=0)
    alarm_type = "Recurrent"
    inhibitors = []

    def dump_runtime(self):
        inhibitors = []
        for inhibitor in self.inhibitors:
            inhibitors.append(inhibitor.dump_runtime())
        return {
            "inhibitors": inhibitors
        }

    def check_runtime(self):
        for inhibitor in self.inhibitors:
            if inhibitor.check_runtime():
                return True
        return False

    def load_configuration(self, configuration, runtime):
        if "days" in configuration:
            self.days = sorted(configuration["days"])
        if "hour" in configuration:
            self.hour = time.fromisoformat(configuration["hour"])
        for i, inhibitor in self.inhibitors:
            inhibitor.load_configuration(configuration["inhibitors"][i], runtime["inhibitors"][i])

    def __init__(self, configuration, runtime):
        self.load_configuration(configuration, runtime)
        self.inhibitors.append(shiva_inhibitor.ShivaInhibitor(configuration["inhibitors"][0], runtime["inhibitors"][0]))
        for inhibitor in self.inhibitors:
            inhibitor.start() 

    def is_next_date_valid(self,next_date, last_alarm):
        difference_with_now = datetime.now() - next_date

        if (difference_with_now.total_seconds() > 15 * 60):
            return False

        if (next_date <= last_alarm):
            return False

        for inhibitor in self.inhibitors:
            if not inhibitor.is_next_date_valid(next_date):
                return False

        return True

    def next_alarm(self, last_alarm):
        if len(self.days) == 0:
            return None

        next_dates = []
        for day in self.days:
            next_date = datetime.combine(date.today(), self.hour)
            day_difference = day - next_date.weekday()
            if day_difference < 0:
                next_date = next_date + timedelta(days=(day_difference + 7))
            elif day_difference > 0:
                next_date = next_date + timedelta(days=(day_difference))
            next_dates.append(next_date)

        for next_date in sorted(next_dates):
            if self.is_next_date_valid(next_date, last_alarm):
                return next_date     
        return None