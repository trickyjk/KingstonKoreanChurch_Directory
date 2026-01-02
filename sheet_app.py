import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests

# 1. 페이지 설정
st.set_page_config(page_title="킹스턴한인교회 교적부", layout="wide")

# 2. 구글 시트 연결 설정
@st.cache_resource
def get_creds():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Streamlit Cloud의 Secrets 사용
    if "gcp_service_account" in st.secrets:
        return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    # 로컬 테스트용
    else:
        return Credentials.from_service_account_file('credentials.json', scopes=scope)

def load_data():
    try:
        creds = get_creds()
        client = gspread.authorize(creds)
        
        # 목사님 시트의 고유 ID를 직접 사용하여 가장 확실하게 연결합니다.
        spreadsheet_id = "1rS7junnoO1AxUWekX1lCD9G1_KWonmXbj2KIZ1wqv_k"
        sheet = client.open_by_key(spreadsheet_id).sheet1 # 첫 번째 탭 자동 선택
        
        data = sheet.get_all_records()
        if not data:
            return None, None
            
        df = pd.DataFrame(data)
        return df, sheet
    except Exception as e:
        st.error(f"데이터 읽기 오류: {e}")
        return None, None

# 3. 데이터 로드
df, sheet = load_data()

if df is not None:
    st.title("📋 킹스턴한인교회 교적부")
    
    # 상단 통계
    col1, col2, col3 = st.columns(3)
    col1.metric("총 인원", f"{len(df)}명")
    
    # 검색창
    search_term = st.text_input("🔍 성도 이름 검색", "")
    
    if search_term:
        filtered_df = df[df['이름'].str.contains(search_term, na=False)]
    else:
        filtered_df = df

    # 성도 카드 목록 출력
    for i in range(0, len(filtered_df), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(filtered_df):
                person = filtered_df.iloc[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # 사진 출력 (URL이 있는 경우)
                        img_url = person.get('사진', '')
                        if img_url and str(img_url).startswith('http'):
                            st.image(img_url, use_container_width=True)
                        else:
                            st.info("사진 없음")
                            
                        st.subheader(person['이름'])
                        st.write(f"**직분:** {person.get('직분', '-')}")
                        st.write(f"**전화:** {person.get('전화번호', '-')}")
                        st.write(f"**주소:** {person.get('주소', '-')}")
                        
                        # 상세 정보 확장
                        with st.expander("상세 정보"):
                            st.write(f"생년월일: {person.get('생년월일', '-')}")
                            st.write(f"이메일: {person.get('이메일', '-')}")
                            st.write(f"가족: {person.get('가족', '-')}")
                            st.write(f"사역/목양노트: {person.get('사역/목양노트', '-')}")

else:
    st.error("데이터를 불러올 수 없습니다. 구글 시트 공유 설정을 다시 확인해 주세요.")
    st.info("공유 이메일: kkc-admin@churchapp-482717.iam.gserviceaccount.com")
