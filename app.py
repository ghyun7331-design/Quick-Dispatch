import streamlit as st
import pandas as pd
import re

# 1. 페이지 설정
st.set_page_config(page_title="Airbus Quick Dispatch", layout="wide")
st.title("✈️ Airbus Quick Dispatch Guide")

# 2. 데이터 로드 (파일 이름을 실제 업로드한 이름과 똑같이 맞췄습니다)
@st.cache_data
def load_data():
    db = pd.read_csv('Quick Dispatch - Quick Dispatch_DB.csv')
    fleet = pd.read_csv('Quick Dispatch - Fleet Mapping DB.csv')
    return db, fleet

db_df, fleet_df = load_data()

# 3. URL 자동 생성 함수
def get_search_url(task_str):
    # 정규표현식: 숫자와 하이픈만 추출하여 검색 URL로 만듦
    clean_id = re.sub(r'[^0-9-]', '', str(task_str))
    return f"https://w3.airbus.com/1T40/search?q={clean_id}"

# 4. 사이드바 필터
st.sidebar.header("필터 설정")
# Fleet Mapping DB를 활용하여 기종 선택
models = fleet_df['A/C Model'].unique()
selected_model = st.sidebar.selectbox("기종 선택 (Model)", models)

# 선택한 기종에 해당하는 Tail Number만 표시
tail_numbers = fleet_df[fleet_df['A/C Model'] == selected_model]['Tail Number (등록기호)'].unique()
selected_tail = st.sidebar.selectbox("Tail Number 선택", tail_numbers)

# 5. 메인 화면: 선택한 기종의 데이터만 필터링하여 표시
st.subheader(f"작업 리스트: {selected_tail} ({selected_model})")

# 기종별 DB 필터링
filtered_db = db_df[db_df['기종 (Model)'] == selected_model]

# 6. 작업 목록 카드 형태로 출력
for _, row in filtered_db.iterrows():
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**[{row['항목 (Section)']}]** {row['작업 (Task Description)']}")
            st.caption(f"Ref: {row['링크 (Reference)']} | 적용: {row['적용 (Effectivity)']}")
        with col2:
            # 클릭 시 검색 URL로 연결
            search_url = get_search_url(row['링크 (Reference)'])
            st.link_button("매뉴얼 검색", search_url)

# 7. 추가: 데이터 검색 기능
st.markdown("---")
st.subheader("데이터베이스 전체 검색")
search_query = st.text_input("작업 내용 검색 (예: Leak, Torque 등)")
if search_query:
    result = filtered_db[filtered_db['작업 (Task Description)'].str.contains(search_query, case=False, na=False)]
    st.dataframe(result, use_container_width=True)