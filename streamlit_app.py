import json
import streamlit as st
import fitz
from datetime import datetime
import os
import requests
from pytz import timezone
from dotenv import load_dotenv

st.title('효성여자고등학교')

today = st.date_input("조회일", value=datetime.now(timezone('Asia/Seoul')))
month = today.month
day = today.day
date_str = f"{month:02}월 {day:02}일"
today_str = today.strftime("%Y%m%d")

filename = "Dinner_Menu.pdf"

load_dotenv()
API_KEY = os.getenv("NEIS_KEY") or st.secrets["NEIS_KEY"]
ATPT_OFCDC_SC_CODE = 'D10'
SD_SCHUL_CODE = '7240106'

tab1, tab2, tab3 = st.tabs(["중식", "석식", "시간표"])

with tab1:
    st.markdown("## 중식 식단")
    url = 'https://open.neis.go.kr/hub/mealServiceDietInfo'
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'ATPT_OFCDC_SC_CODE': ATPT_OFCDC_SC_CODE,
        'SD_SCHUL_CODE': SD_SCHUL_CODE,
        'MLSV_YMD': today_str
    }
    try:
        res = requests.get(url, params=params, timeout=30)
        data = res.json()
        meals = data['mealServiceDietInfo'][1]['row'][0]['DDISH_NM']
        cleaned = meals.replace('<br/>', '\n')
        for item in cleaned.strip().split('\n'):
            st.markdown(f"- {item.strip()}")
    except Exception:
        st.error("중식 정보가 없습니다.")

with tab2:
    st.markdown("## 석식 식단")
    if not os.path.exists(filename):
        st.error("석식 정보가 없습니다.")
    else:
        try:
            doc = fitz.open(filename)
            found = False
            for page in doc:
                tables = page.find_tables()
                if not tables:
                    continue
                for table in tables:
                    data = table.extract()
                    for row_idx, row in enumerate(data):
                        for col_idx, cell in enumerate(row):
                            if cell and date_str in cell:
                                next_row_idx = row_idx + 1
                                if next_row_idx < len(data):
                                    next_row = data[next_row_idx]
                                    if len(next_row) > col_idx:
                                        content = next_row[col_idx]
                                        menu_items = content.strip().split("\n")
                                        menu_items.pop()
                                        if menu_items == [""] or menu_items == [",,,,,"]:
                                             st.error(f"석식 정보가 없습니다.")
                                        else:
                                            for item in menu_items:
                                                st.markdown(f"- {item.strip()}")
                                        found = True
                                break
                        if found:
                            break
                    if found:
                        break
                if found:
                    break
            if not found:
                st.error("석식 정보가 없습니다.")
        except Exception as e:
            st.error("파싱 과정 중 오류가 발생했습니다.")
            st.exception(e)
            
with tab3:
    st.markdown("## 시간표")

    grade = st.selectbox("학년", ["1", "2", "3"], index=0)
    class_nm = st.selectbox("반", [str(i) for i in range(1, 10)], index=0)

    url = 'https://open.neis.go.kr/hub/hisTimetable'
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'ATPT_OFCDC_SC_CODE': ATPT_OFCDC_SC_CODE,
        'SD_SCHUL_CODE': SD_SCHUL_CODE,
        'GRADE': grade,
        'CLASS_NM': class_nm,
        'ALL_TI_YMD': today_str
    }

    try:
        res = requests.get(url, params=params, stream=True, timeout=15)
        raw = res.raw.read(decode_content=True)
        data = json.loads(raw)
        timetable = data['hisTimetable'][1]['row']
        for period in timetable:
            st.text(f"{period['PERIO']}교시: {period['ITRT_CNTNT']}")
    except Exception as e:
        st.error("시간표 정보를 불러올 수 없습니다.")
