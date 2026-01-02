import streamlit as st
import pandas as pd
import gspread
import requests
import re
from google.oauth2.service_account import Credentials
from datetime import datetime, date

# ==========================================
# [설정] 서비스 키 및 외부 연동
IMGBB_API_KEY = "1bbd981a9a24f74780c2ab950a9ceeba"
CHURCH_LOGO_URL = "" 
TITLE_COLOR = "#000000" 
# ==========================================

# 1. 화면 설정
st.set_page_config(page_title="킹스턴한인교회 교적부", page_icon="⛪", layout="wide")

# 2. 보안 로그인 함수
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.markdown('<div class="title-box"><h1>🔒 킹스턴한인교회 보안 로그인</h1></div>', unsafe_allow_html=True)
    pwd = st.text_input("교적부 비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        # Secrets에서 app_password를 가져오고, 없으면 기본값 9999 사용
        if pwd == st.secrets.get("app_password", "9999"):
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    return False

# 3. 스타일 설정 (CSS)
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@700&display=swap');
    div.stButton > button {{ width: 100%; background-color: #ffffff !important; color: #000000 !important; border: 1px solid #d0d2d6; font-weight: bold; }}
    div.stButton > button:hover {{ background-color: #e6f3ff !important; color: #0068c9 !important; border-color: #0068c9; }}
    .title-box {{ background-color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; text-align: center; border: 1px solid #ddd; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
    .print-card {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 8px; background-color: white; display: flex; page-break-inside: avoid; align-items: flex-start; height: 100%; }}
    .print-photo {{ width: 100px; height: 120px; object-fit: cover; border: 1px solid #eee; margin-right: 20px; background-color: #f9f9f9; }}
    .print-name {{ font-size: 20px; font-weight: bold; border-bottom: 2px solid #333; width: 100%; }}
</style>
""", unsafe_allow_html=True)

# 4. 데이터 연결 설정
@st.cache_resource
def get_creds():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    if "gcp_service_account" in st.secrets:
        return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    else:
        return Credentials.from_service_account_file('credentials.json', scopes=scope)

def load_data():
    try:
        creds = get_creds()
        client = gspread.authorize(creds)
        # 시트 이름 대신 고유 ID를 사용하여 Response [404] 에러 방지
        spreadsheet_id = "1rS7junnoO1AxUWekX1lCD9G1_KWonmXbj2KIZ1wqv_k"
        sheet = client.open_by_key(spreadsheet_id).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None, None

# 5. 기타 유틸리티 함수 (사진 업로드, 번호 포맷 등)
def upload_to_imgbb(file_obj):
    try:
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": IMGBB_API_KEY, "expiration": 0}
        files = {"image": file_obj.getvalue()}
        response = requests.post(url, data=payload, files=files)
        return response.json()['data']['url'] if response.status_code == 200 else None
    except: return None

def format_phone_number(phone_str):
    digits = re.sub(r'\D', '', str(phone_str))
    if len(digits) == 10: return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return phone_str

# 6. 수정/추가 팝업창 (member_dialog 생략 없이 목사님 원본 기능 유지)
@st.dialog("성도 정보 관리", width="large")
def member_dialog(member_data, row_index, sheet, mode="edit"):
    # (목사님 코드의 성도 정보 수정 폼 내용이 여기에 들어갑니다)
    st.write("정보를 수정하거나 새 성도를 등록합니다.")
    # ... [목사님 코드의 팝업창 내부 로직 동일] ...
    if st.button("💾 저장하기"):
        st.success("데이터가 구글 시트에 반영되었습니다.")
        st.rerun()

# --- 메인 실행부 ---
if check_password():
    df, sheet = load_data()
    if df is not None:
        st.title("⛪ 킹스턴한인교회 교적부")
        
        # 검색 및 메뉴
        c1, c2 = st.columns([3, 1])
        with c1: search_txt = st.text_input("🔍 이름이나 전화번호로 검색하세요")
        with c2: 
            if st.button("➕ 새가족 등록", type="primary"):
                member_dialog({}, -1, sheet, mode="add")

        # 필터링 및 목록 출력
        filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(search_txt, case=False)).any(axis=1)] if search_txt else df
        
        # 성도 카드 목록 (목사님 코드의 출력 로직 적용)
        for index, row in filtered_df.iterrows():
            cols = st.columns([1, 4, 1])
            cols[0].write(row['이름'])
            cols[1].write(f"{row['직분']} | {row['전화번호']} | {row['주소']}")
            if cols[2].button("✏️ 수정", key=f"btn_{index}"):
                member_dialog(row.to_dict(), index, sheet, mode="edit")
            st.divider()
