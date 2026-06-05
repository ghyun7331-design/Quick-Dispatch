import streamlit as st
import pandas as pd
import re

# 1. 페이지 설정 (모바일 최적화 및 전체 너비 사용)
st.set_page_config(page_title="Airbus Quick Dispatch", layout="wide")

# 1-1. 제목을 무조건 한 줄로 표시하고 화면에 맞춰 자동 축소하는 CSS 설정
st.markdown(
    """
    <style>
    .responsive-title {
        font-size: clamp(1.2rem, 4vw, 2.5rem); /* 화면 크기에 따라 글자 크기가 유연하게 변함 */
        white-space: nowrap; /* 절대 줄바꿈을 허용하지 않음 */
        font-weight: bold;
        padding-bottom: 20px;
    }
    </style>
    <div class="responsive-title">✈️ Airbus Quick Dispatch Guide</div>
    """,
    unsafe_allow_html=True
)

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

# 4. FSN 적용 여부 확인 함수 (Effectivity 스마트 필터링)
def check_effectivity(fsn, eff_str):
    if pd.isna(eff_str): return True 
    eff_str = str(eff_str).upper()
    if 'ALL' in eff_str: return True 
    
    fsn_str = str(fsn).strip()
    if not fsn_str or fsn_str == 'NAN': return True 
    
    # 단순 포함 여부 확인
    if fsn_str in eff_str:
        return True
    
    # 범위(001-050 등) 확인
    ranges = re.findall(r'(\d+)\s*-\s*(\d+)', eff_str)
    try:
        fsn_int = int(fsn_str)
        for start, end in ranges:
            if int(start) <= fsn_int <= int(end):
                return True
    except ValueError:
        pass 
        
    return False

# 5. 사이드바 필터 설정
st.sidebar.header("필터 설정")

# [업데이트] A320 포함 및 화면 표시(A321)와 검색(321) 분리
display_models = ['A320', 'A321', 'A330', 'A350', 'A380']
selected_display = st.sidebar.selectbox("기종 그룹 (Base Model)", display_models)

# DB 검색을 위해 선택된 값에서 'A'를 제거 (예: 'A321' -> '321')
selected_base = selected_display.replace('A', '')

# Fleet DB에서 기종 필터링
filtered_fleet = fleet_df[fleet_df['A/C Model'].astype(str).str.contains(selected_base, na=False)]
tail_numbers = filtered_fleet['Tail Number (등록기호)'].unique()

if len(tail_numbers) == 0:
    st.warning(f"데이터베이스에 {selected_display} 기종에 해당하는 Tail Number가 없습니다.")
    st.stop()

selected_tail = st.sidebar.selectbox("Tail Number 선택", tail_numbers)

# 6. FSN 매칭 로직
fsn_value = filtered_fleet[filtered_fleet['Tail Number (등록기호)'] == selected_tail]['FSN'].values[0]
st.sidebar.info(f"✈️ 선택된 호기 FSN: **{fsn_value}**")

# Dispatch DB 1, 2차 필터링
filtered_db_by_model = db_df[db_df['기종 (Model)'].astype(str).str.contains(selected_base, na=False)]
filtered_db_by_eff = filtered_db_by_model[filtered_db_by_model['적용 (Effectivity)'].apply(lambda x: check_effectivity(fsn_value, x))]

# 7. 항목(Section) 필터링
if '항목 (Section)' in filtered_db_by_eff.columns and not filtered_db_by_eff.empty:
    sections = ['전체 (All)'] + filtered_db_by_eff['항목 (Section)'].unique().tolist()
    selected_section = st.sidebar.selectbox("항목 (Section) 선택", sections)
    
    if selected_section != '전체 (All)':
        final_filtered_db = filtered_db_by_eff[filtered_db_by_eff['항목 (Section)'] == selected_section]
    else:
        final_filtered_db = filtered_db_by_eff
else:
    final_filtered_db = filtered_db_by_eff

# 8. 메인 화면 출력
st.subheader(f"작업 리스트: {selected_tail} (FSN: {fsn_value})")

if final_filtered_db.empty:
    st.warning("선택하신 호기(FSN)에 해당하는 적용(Effectivity) 작업이 없습니다.")
else:
    for _, row in final_filtered_db.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**[{row['항목 (Section)']}]** {row['작업 (Task Description)']}")
                st.caption(f"Ref: {row['링크 (Reference)']} | 적용: **{row['적용 (Effectivity)']}**")
            with col2:
                search_url = get_search_url(row['링크 (Reference)'])
                st.link_button("매뉴얼 검색", search_url)

# 9. 데이터 전체 검색 기능
st.markdown("---")
st.subheader("데이터베이스 전체 검색")
search_query = st.text_input("검색어를 입력하세요 (예: Door, Leak 등)")
if search_query:
    result = final_filtered_db[final_filtered_db['작업 (Task Description)'].str.contains(search_query, case=False, na=False)]
    st.dataframe(result, use_container_width=True)
