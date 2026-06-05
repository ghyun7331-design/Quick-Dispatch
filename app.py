import streamlit as st
import pandas as pd
import re

# 1. 페이지 설정
st.set_page_config(page_title="Airbus Quick Dispatch", layout="wide")
st.title("✈️ Airbus Quick Dispatch Guide")

# 2. 데이터 로드
@st.cache_data
def load_data():
    db = pd.read_csv('Quick Dispatch - Quick Dispatch_DB.csv')
    fleet = pd.read_csv('Quick Dispatch - Fleet Mapping DB.csv')
    return db, fleet

db_df, fleet_df = load_data()

# 3. URL 자동 생성 함수
def get_search_url(task_str):
    clean_id = re.sub(r'[^0-9-]', '', str(task_str))
    return f"https://w3.airbus.com/1T40/search?q={clean_id}"

# 4. 사이드바 필터 설정
st.sidebar.header("필터 설정")

# 기종 선택
models = fleet_df['A/C Model'].unique()
selected_model = st.sidebar.selectbox("기종 선택 (Model)", models)

# Tail Number 선택
tail_numbers = fleet_df[fleet_df['A/C Model'] == selected_model]['Tail Number (등록기호)'].unique()
selected_tail = st.sidebar.selectbox("Tail Number 선택", tail_numbers)

# **[수정됨] 항목(Section) 필터 추가**
filtered_db_by_model = db_df[db_df['기종 (Model)'] == selected_model]
sections = ['전체 (All)'] + filtered_db_by_model['항목 (Section)'].unique().tolist()
selected_section = st.sidebar.selectbox("항목 (Section) 선택", sections)

# 5. 메인 화면 로직
st.subheader(f"작업 리스트: {selected_tail} ({selected_model})")

# 데이터 필터링 적용
filtered_db = filtered_db_by_model.copy()
if selected_section != '전체 (All)':
    filtered_db = filtered_db[filtered_db['항목 (Section)'] == selected_section]

# 6. 작업 목록 카드 출력
if filtered_db.empty:
    st.warning("선택하신 조건에 해당하는 작업이 없습니다.")
else:
    for _, row in filtered_db.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**[{row['항목 (Section)']}]** {row['작업 (Task Description)']}")
                st.caption(f"Ref: {row['링크 (Reference)']} | 적용: {row['적용 (Effectivity)']}")
            with col2:
                search_url = get_search_url(row['링크 (Reference)'])
                st.link_button("매뉴얼 검색", search_url)

# 7. 데이터 전체 검색 기능
st.markdown("---")
st.subheader("데이터베이스 전체 검색")
search_query = st.text_input("검색어를 입력하세요 (예: 32-00, Door, Leak 등)")
if search_query:
    result = filtered_db_by_model[filtered_db_by_model['작업 (Task Description)'].str.contains(search_query, case=False, na=False)]
    st.dataframe(result, use_container_width=True)
