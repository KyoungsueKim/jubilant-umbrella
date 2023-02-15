import datetime
import sys

import pandas as pd


def clear_caches():
    from main import Main
    Main.captcha.clear()
    Main.takingLessonsFrame.clear()

    print("[Caches Clear]", file=sys.stderr)


def is_open_time():
    current_time = datetime.datetime.now().minute
    if 0 <= current_time % 10 < 5:
        return True
    return False


def get_taking_lesson(client_id: str):
    from main import Main

    return Main.takingLessonsFrame[client_id] if client_id in Main.takingLessonsFrame.keys() else pd.DataFrame(
        columns=['sbjName', 'sbjCode', 'profName', 'credit', 'hours', 'time'])
