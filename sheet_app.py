import streamlit as st
import pandas as pd
import gspread
import requests
import re
from google.oauth2.service_account import Credentials
from datetime import datetime, date

# 1. 설정 및 화면 구성
st.set_page_config(page_title="킹스턴한인교회 교적부", page_icon="⛪", layout="wide")

# 스타일 설정
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@700&display=swap');
    div.stButton > button { width: 100%; background-color: #ffffff !important; color: #000000 !important; border: 1px solid #d0d2d6; font-weight: bold; }
    .title-box { background-color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; text-align: center; border: 1px solid #ddd; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .print-card { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 8px; background-color: white; display: flex; page-break-inside: avoid; align-items: flex-start; height: 100%; }
    .print-photo { width: 100px; height: 120px; object-fit: cover; border: 1px solid #eee; margin-right: 20px; }
    .print-name { font-size: 20px; font-weight: bold; border-bottom: 2px solid #333; padding-bottom: 5px; width: 100%; }
</style>
""", unsafe_allow_html=True)

# 2. 데이터 연결 (인증 에러 자동 보정 로직)
@st.cache_resource
def load_data():
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        sa_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in sa_info:
            key = sa_info["private_key"].replace("\\n", "\n").strip().replace('"', '')
            sa_info["private_key"] = key
        creds = Credentials.from_service_account_info(sa_info, scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet_id = "1rS7junnoO1AxUWekX1lCD9G1_KWonmXbj2KIZ1wqv_k"
        sheet = client.open_by_key(spreadsheet_id).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except Exception as e:
        st.error(f"⚠️ 데이터 연결 실패: {e}")
        return None, None

# 3. 유틸리티 함수
def format_phone_number(phone_str):
    if not phone_str: return ""
    digits = re.sub(r'\D', '', str(phone_str))
    if len(digits) == 10: return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11: return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return phone_str

def generate_card_html(person, selected_cols):
    photo_val = str(person.get('사진', ''))
    img_tag = f'<img src="{photo_val}" class="print-photo">' if photo_val.startswith('http') else '<div style="width:100px; height:120px; background:#f0f0f0; display:flex; align-items:center; justify-content:center; margin-right:20px;">사진없음</div>'
    info_html = ""
    for col in selected_cols:
        val = person.get(col, '')
        if val: info_html += f'<div style="font-size:14px; margin-bottom:3px;"><b>{col}:</b> {val}</div>'
    return f'<div class="print-card">{img_tag}<div style="flex:1;"><div class="print-name">{person.get("이름", "")} <span style="font-size:14px; font-weight:normal;">{person.get("직분", "")}</span></div>{info_html}</div></div>'

# 4. 성도 정보 상세 관리 팝업
@st.dialog("성도 정보 관리", width="large")
def member_dialog(member_data, row_index, sheet, mode="edit"):
    role_options = ['성도', '서리집사', '안수집사', '협동안수집사', '은퇴안수집사', '시무권사', '협동권사', '은퇴권사', '장로', '협동장로', '은퇴장로', '협동목사', '목사']
    def get_val(col): return member_data.get(col, "") if mode == "edit" else ""
    with st.form("member_form"):
        uploaded_file = st.file_uploader("사진 선택", type=['png', 'jpg', 'jpeg'])
        updated_data = {}
        c1, c2 = st.columns(2)
        with c1: updated_data['이름'] = st.text_input("이름", value=str(get_val('이름')))
        with c2:
            val = str(get_val('직분')); idx = role_options.index(val) if val in role_options else 0
            updated_data['직분'] = st.selectbox("직분", role_options, index=idx)
        updated_data['전화번호'] = st.text_input("전화번호", value=str(get_val('전화번호')))
        updated_data['주소'] = st.text_input("주소", value=str(get_val('주소')))
        updated_data['목양노트'] = st.text_area("목양노트", value=str(get_val('목양노트')), height=200)
        if st.form_submit_button("💾 저장하기", type="primary"):
            updated_data['전화번호'] = format_phone_number(updated_data['전화번호'])
            headers = sheet.row_values(1)
            row_values = [updated_data.get(h, member_data.get(h, "")) for h in headers]
            if mode == "edit": sheet.update(range_name=f"A{row_index+2}", values=[row_values])
            else: sheet.append_row(row_values)
            st.success("반영되었습니다!"); st.rerun()

# --- 메인 실행부 ---
df, sheet = load_data()
if df is not None:
    with st.sidebar:
        st.header("🖨️ 인쇄 설정")
        print_mode = st.toggle("주소록 인쇄 모드", value=False)
        if print_mode:
            selected_cols = st.multiselect("인쇄 항목", [c for c in df.columns if c not in ['사진', '이름']], default=['직분', '전화번호', '주소'])
    if print_mode:
        st.markdown('<div class="title-box"><h1>2026 킹스턴한인교회 주소록</h1></div>', unsafe_allow_html=True)
        for i in range(0, len(df), 2):
            cols = st.columns(2)
            for j in range(2):
                if i+j < len(df):
                    with cols[j]: st.markdown(generate_card_html(df.iloc[i+j], selected_cols), unsafe_allow_html=True)
    else:
        st.title("⛪ 킹스턴한인교회 교적부")
        c1, c2 = st.columns([3, 1])
        with c1: search = st.text_input("🔍 성도 검색")
        with c2: 
            st.write(""); 
            if st.button("➕ 새가족 등록"): member_dialog({}, -1, sheet, mode="add")
        f_df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)] if search else df
        for idx, row in f_df.iterrows():
            cols = st.columns([1, 4, 1])
            cols[0].write(f"**{row.get('이름', '')}**")
            cols[1].write(f"{row.get('직분', '')} | {row.get('전화번호', '')} | {row.get('주소', '')}")
            if cols[2].button("✏️ 수정", key=f"e_{idx}"): member_dialog(row.to_dict(), idx, sheet, mode="edit")
            st.divider()
