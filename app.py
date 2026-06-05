import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Airbus Quick Dispatch", layout="wide")
st.title("✈️ Airbus Quick Dispatch Guide")

@st.cache_data
def load_data():
    db = pd.read_csv('Quick Dispatch - Quick Dispatch_DB.csv')
    fleet = pd.read_csv('Quick Dispatch - Fleet Mapping DB.csv')
    return db, fleet

db_df, fleet_df = load_data()

# --- 디버그 정보 출력 ---
st.sidebar.markdown("---")
st.sidebar.subheader("DEBUG (데이터 확인)")
# -----------------------

st.sidebar.header("필터 설정")
models = fleet_df['A/C Model'].unique()
selected_model = st.sidebar.selectbox("기종 선택 (Model)", models)

# 데이터 필터링 단계
filtered_db_by_model = db_df[db_df['기종 (Model)'] == selected_model]

# --- 디버그 출력 ---
st.sidebar.write(f"현재 선택된 기종: {selected_model}")
st.sidebar.write(f"조회된 작업 개수: {len(filtered_db_by_model)}개")
st.sidebar.write(f"컬럼 목록: {list(db_df.columns)}")
# ------------------

tail_numbers = fleet_df[fleet_df['A/C Model'] == selected_model]['Tail Number (등록기호)'].unique()
selected_tail = st.sidebar.selectbox("Tail Number 선택", tail_numbers)

# 항목(Section) 필터
if '항목 (Section)' in db_df.columns:
    sections = ['전체 (All)'] + filtered_db_by_model['항목 (Section)'].unique().tolist()
    selected_section = st.sidebar.selectbox("항목 (Section) 선택", sections)
else:
    st.sidebar.error("CSV에 '항목 (Section)' 컬럼이 없습니다!")
    selected_section = '전체 (All)'

# (이후 코드는 동일하므로 생략 - 그대로 두셔도 됩니다)
# [이미 작성하신 나머지 코드를 이 아래에 그대로 붙이시면 됩니다]
