from datetime import datetime
import calendar


class DateTools:
    @staticmethod
    def get_ordinal_suffix(day):
        special_cases = {
            1: 'first',
            2: 'second',
            3: 'third',
            4: 'fourth',
            5: 'fifth',
            6: 'sixth',
            7: 'seventh',
            8: 'eighth',
            9: 'ninth',
            10: 'tenth',
            11: 'eleventh',
            12: 'twelfth',
            13: 'thirteenth',
            14: 'fourteenth',
            15: 'fifteenth',
            16: 'sixteenth',
            17: 'seventeenth',
            18: 'eighteenth',
            19: 'nineteenth',
            20: 'twentieth',
            21: 'twenty-first',
            22: 'twenty-second',
            23: 'twenty-third',
            24: 'twenty-fourth',
            25: 'twenty-fifth',
            26: 'twenty-sixth',
            27: 'twenty-seventh',
            28: 'twenty-eighth',
            29: 'twenty-ninth',
            30: 'thirtieth',
            31: 'thirty-first'
        }
        return special_cases.get(day, f"{day}th")

    @staticmethod
    def human_readable_date(date):
        month = date.strftime("%B")
        day = date.day
        year = date.year
        day_with_suffix = DateTools.get_ordinal_suffix(day)
        day_name = calendar.day_name[date.weekday()]
        return f"{day_name} {month} {day_with_suffix} {year}"

    @staticmethod
    def human_readable_time(date: datetime) -> str:
        return date.strftime('%I:%M %p')
