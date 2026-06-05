import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Airbus Quick Dispatch", layout="wide")
st.title("✈️ Airbus Quick Dispatch Guide")

@st.cache_data
def load_data():
    try:
        db = pd.read_csv('Quick Dispatch - Quick Dispatch_DB.csv')
        fleet = pd.read_csv('Quick Dispatch - Fleet Mapping DB.csv')
        return db, fleet
    except Exception as e:
        st.error(f"파일 로드 에러: {e}")
        return None, None

db_df, fleet_df = load_data()

if db_df is not None and fleet_df is not None:
    # --- 디버깅: CSV 컬럼 확인 ---
    # 만약 항목이 안 나오면 아래 리스트를 보고 CSV 파일의 글자와 비교해보세요
    # st.write("확인용 컬럼 목록:", db_df.columns.tolist()) 

    def get_search_url(task_str):
        clean_id = re.sub(r'[^0-9-]', '', str(task_str))
        return f"https://w3.airbus.com/1T40/search?q={clean_id}"

    st.sidebar.header("필터 설정")
    models = fleet_df['A/C Model'].unique()
    selected_model = st.sidebar.selectbox("기종 선택 (Model)", models)

    tail_numbers = fleet_df[fleet_df['A/C Model'] == selected_model]['Tail Number (등록기호)'].unique()
    selected_tail = st.sidebar.selectbox("Tail Number 선택", tail_numbers)

    # 필터링 로직
    filtered_db_by_model = db_df[db_df['기종 (Model)'] == selected_model]
    
    # [중요] 컬럼 이름이 정확히 일치하는지 다시 확인해주세요
    if '항목 (Section)' in filtered_db_by_model.columns:
        sections = ['전체 (All)'] + filtered_db_by_model['항목 (Section)'].unique().tolist()
        selected_section = st.sidebar.selectbox("항목 (Section) 선택", sections)
    else:
        st.error("데이터 파일에 '항목 (Section)' 컬럼이 없습니다. CSV 파일의 헤더를 확인하세요.")
        selected_section = '전체 (All)'

    st.subheader(f"작업 리스트: {selected_tail} ({selected_model})")

    filtered_db = filtered_db_by_model.copy()
    if selected_section != '전체 (All)':
        filtered_db = filtered_db[filtered_db['항목 (Section)'] == selected_section]

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

    st.markdown("---")
    st.subheader("데이터베이스 전체 검색")
    search_query = st.text_input("검색어를 입력하세요")
    if search_query:
        result = filtered_db_by_model[filtered_db_by_model['작업 (Task Description)'].str.contains(search_query, case=False, na=False)]
        st.dataframe(result, use_container_width=True)
