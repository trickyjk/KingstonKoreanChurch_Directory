import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 페이지 설정
st.set_page_config(page_title="킹스턴한인교회 교적부", layout="wide")

# 비밀번호 체크 함수
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.title("🔒 보안 로그인")
    pwd = st.text_input("교적부 비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        if pwd == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    return False

# 데이터 로드 함수
@st.cache_resource
def load_data():
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # 목사님 시트 ID
        spreadsheet_id = "1rS7junnoO1AxUWekX1lCD9G1_KWonmXbj2KIZ1wqv_k"
        sheet = client.open_by_key(spreadsheet_id).sheet1
        
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"데이터 연결 실패: {e}")
        return None

# 실행
if check_password():
    df = load_data()
    if df is not None:
        st.title("📋 킹스턴한인교회 교적부")
        
        # 검색 기능
        search = st.text_input("🔍 성도 이름 검색")
        view_df = df[df['이름'].str.contains(search, na=False)] if search else df
        
        # 목록 출력 (4열 배치)
        for i in range(0, len(view_df), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(view_df):
                    p = view_df.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            if p.get('사진') and str(p['사진']).startswith('http'):
                                st.image(p['사진'], use_container_width=True)
                            st.subheader(p['이름'])
                            st.write(f"**직분:** {p.get('직분', '-')}")
                            st.write(f"**전화:** {p.get('전화번호', '-')}")
                            with st.expander("상세 정보"):
                                st.write(f"주소: {p.get('주소', '-')}")
                                st.write(f"가족: {p.get('가족', '-')}")
