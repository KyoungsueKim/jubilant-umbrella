import glob
import json
import os.path
import random
import re
import uuid

import uvicorn
import pandas as pd

from core import *
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse

MAX_CREDIT = "24"
GRADE = "1"
STUDENT_DEPARTMENT = "무화과"
STUDENT_NUMBER = "202320001"
NAME = "홍길동"

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
db = pd.read_excel('static/db/db.xlsx', engine='openpyxl', header=1, usecols="D, E, G, I, J, Q", names=['sbjName', 'sbjCode', 'profName', 'credit', 'hours', 'time'])


@app.middleware("http")
async def add_client_id(request: Request, call_next):
    client_id: str = request.cookies.get("client_id")

    if client_id is None:
        client_id = str(uuid.uuid4())
        response = await call_next(request)
        response.set_cookie(key="client_id", value=client_id)
        return response
    request.client_id = client_id
    response = await call_next(request)
    return response


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    메인 페이지
    :param request:
    :return: HtmlTemplate
    """
    html: str = "index.html" if is_open_time() else "index_none.html"
    return templates.TemplateResponse(html, {"request": request, "name": NAME, "stdNumber": STUDENT_NUMBER, "stdDept": STUDENT_DEPARTMENT, "grade": GRADE, "maxCredits": MAX_CREDIT})


@app.post("/saveTlsnNoAply.ajax")
async def saveTlsnNoAply(request: Request):
    """
    과목 수강 신청.
    :param request:
    :return:
    """
    client_id: str = request.cookies['client_id']
    body: bytes = (await request.body()).decode()
    data: dict = json.loads(body)
    taking_lessons = get_taking_lesson(client_id)

    # 인증 번호 맞는지 확인.
    if captcha[client_id] != data['securityNumber']:
        return {"RESULT_MESG": "인증번호를 정확히 입력하세요", "MESSAGE_CODE": -1}

    # 입력된 과목 코드로부터 슬롯 하나 때와서 slot 변수에 저장
    sbjCode: str = data['strTlsnNo'].upper()
    slot = db.loc[db['sbjCode'] == sbjCode]

    # 과목 이름 추출. 만약 검색된 이름이 없다면
    sbjName = slot['sbjName'].values[0] if slot['sbjName'].shape[0] == 1 else None
    if sbjName is None:
        return {"RESULT_MESG": "과목코드가 올바르지 않습니다.", "MESSAGE_CODE": -1}

    # 최대 학점 제한을 넘은 경우
    elif taking_lessons['credit'].sum() + slot['credit'].sum() > int(MAX_CREDIT):
        return {"RESULT_MESG": "최대 이수 학점을 초과하였습니다.", "MESSAGE_CODE": -1}

    # 해당 과목이 이미 수강중인 과목이라면
    elif taking_lessons.loc[taking_lessons['sbjName'] == sbjName].shape[0] > 0:
        return {"RESULT_MESG": "이미 수강중인 과목입니다.", "MESSAGE_CODE": -1}

    else:
        taking_lessons = pd.concat([taking_lessons, slot])
        takingLessonsFrame[client_id] = taking_lessons
        return {"RESULT_MESG": f"[{sbjName}]: 신청완료되었습니다.", "MESSAGE_CODE": 1}


@app.post("/findTakingLessonInfo.ajax")
async def findTakingLessonInfo(request: Request):
    client_id: str = request.cookies['client_id']
    taking_lessons = get_taking_lesson(client_id)

    taking_lesson_info_list = []
    for i in range(taking_lessons.shape[0]):
        SBJT_POSI_FG = 'U0201001'
        TLSN_DEL_POSB_YN = '1'
        CLSS_NO = '1'
        SBJT_KOR_NM = taking_lessons['sbjName'].values[i]
        TLSN_NO = taking_lessons['sbjCode'].values[i]
        MA_LECTURER_KOR_NM = taking_lessons['profName'].values[i]
        PNT = taking_lessons['credit'].values[i]
        TM = taking_lessons['hours'].values[i]
        LT_TM_NM = taking_lessons['time'].values[i]

        # 시간표 str로 장소를 뽑아내 room에 저장.
        time = LT_TM_NM
        if taking_lessons.isnull()['time'].values[0] == True:
            time = '()'
        room = re.compile('\(.*?\)').search(time).group()
        if room is not None:
            room = room[1:-1]

        LT_ROOM_NM = room

        taking_lesson_info_list.append({
            'TLSN_NO': TLSN_NO,
            "PNT": PNT,
            "LT_TM_NM": LT_TM_NM,
            "TM": TM,
            "MA_LECTURER_KOR_NM": MA_LECTURER_KOR_NM,
            "SBJT_POSI_FG": SBJT_POSI_FG,
            "TLSN_DEL_POSB_YN": TLSN_DEL_POSB_YN,
            "LT_ROOM_NM": LT_ROOM_NM,
            "SBJT_KOR_NM": SBJT_KOR_NM,
            "CLSS_NO": CLSS_NO
        })

    return {"RESULT_CODE": "100",
    "loginStatus": "SUCCESS",
    "takingLessonInfoList": [taking_lesson_info_list, []],
    "strTlsnScheValidChkMsg": "상세 일정은 공지사항을 참조하시기 바랍니다.",
    "strTlsnScheValidation": "0",
    "loginStatusMsg": ""}


@app.post("/deleteOpenLectureReg.ajax")
async def deleteOpenLectureReg(request: Request):
    client_id: str = request.cookies['client_id']
    body: bytes = (await request.body()).decode()
    data = json.loads(body)
    taking_lessons = get_taking_lesson(client_id)

    # app.takingLessonsFrame 에서 과목 코드에 해당하는 슬롯 하나 때와서 인덱스 추출 후 index 변수에 저장
    sbjCode = data['strTlsnNo']
    slot = taking_lessons.loc[taking_lessons['sbjCode'] == sbjCode]
    index = slot.index[0] if slot.shape[0] == 1 else None
    if index is not None:
        taking_lessons.drop([index], axis=0, inplace=True)
        return {"RESULT_MESG": f"[{sbjCode}]: 삭제완료되었습니다.", "MESSAGE_CODE": 1}
    else:
        return {"RESULT_MESG": f"과목이 존재하지 않습니다.", "MESSAGE_CODE": -1}

@app.get("/captchaAnswer")
async def captchaAnswer(request: Request):
    return await captchaImg(request)


@app.post("/captchaAnswer")
async def captchaAnswer(request: Request):
    client_id = request.cookies['client_id']
    body = (await request.body()).decode()
    parameters = dict(x.split("=") for x in body.split("&"))
    answer = parameters.get("answer")
    return '200' if captcha[client_id] == answer else '300'


@app.get("/captchaImg")
async def captchaImg(request: Request):
    try:
        img_list = glob.glob('static/images/captcha/*.png')
        img_path = random.sample(img_list, 1)
        number = os.path.basename(img_path[0])[0:4]
        captcha[request.cookies['client_id']] = number

        return FileResponse(img_path[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=80)
