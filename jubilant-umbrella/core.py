import datetime
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

captcha = {}
takingLessonsFrame = {}


def clear_caches():
    captcha = {}
    takingLessonsFrame = {}


scheduler = BackgroundScheduler()
scheduler.add_job(func=clear_caches, trigger="interval", minutes=5,
                  start_date=datetime.datetime.now() + datetime.timedelta(minutes=5),
                  end_date=datetime.datetime(2099, 12, 31))
scheduler.start()


def is_open_time():
    current_time = datetime.datetime.now().minute
    if 0 <= current_time % 10 < 5:
        return True
    return False


def get_taking_lesson(client_id: str):
    return takingLessonsFrame[client_id] if client_id in takingLessonsFrame.keys() else pd.DataFrame(
        columns=['sbjName', 'sbjCode', 'profName', 'credit', 'hours', 'time'])
