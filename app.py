import streamlit as st
import pandas as pd
import re

# 1. 페이지 설정 (모바일 최적화 및 전체 너비 사용)
st.set_page_config(page_title="Airbus Quick Dispatch", layout="wide")

st.markdown(
    """
    <style>
    .responsive-title {
        font-size: clamp(1.2rem, 4vw, 2.5rem);
        white-space: nowrap;
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

# 4. [강화됨] FSN 적용 여부 확인 함수 (정밀 필터링)
def check_effectivity(fsn_str, eff_str):
    if pd.isna(eff_str): return True 
    eff_str = str(eff_str).upper()
    if 'ALL' in eff_str: return True 
    
    if not fsn_str or fsn_str == 'NAN': return True 
    
    # 정비 데이터의 무결성을 위해 정규식으로 범위와 개별 숫자를 완벽히 분리
    ranges = re.findall(r'(\d+)\s*-\s*(\d+)', eff_str)
    singles = re.findall(r'\b(\d+)\b', eff_str)
    
    try:
        fsn_int = int(fsn_str)
        # 1. 범위 (예: 054-099) 안에 들어가는지 철저히 확인
        for start, end in ranges:
            if int(start) <= fsn_int <= int(end):
                return True
        # 2. 콤마로 구분된 개별 숫자 (예: 151)와 정확히 일치하는지 확인
        for s in singles:
            if int(s) == fsn_int:
                return True
    except ValueError:
        # FSN이 숫자가 아닌 특수 문자열일 경우를 위한 예비책
        if fsn_str in eff_str:
            return True
            
    return False

# 5. 사이드바 필터 설정
st.sidebar.header("필터 설정")

display_models = ['A321 (318/319/320 포함)', 'A330', 'A350', 'A380']
selected_display = st.sidebar.selectbox("기종 그룹 (Base Model)", display_models)

if 'A321' in selected_display:
    search_pattern = '318|319|320|321'
elif 'A330' in selected_display:
    search_pattern = '330'
elif 'A350' in selected_display:
    search_pattern = '350'
elif 'A380' in selected_display:
    search_pattern = '380'
else:
    search_pattern = ''

filtered_fleet = fleet_df[fleet_df['A/C Model'].astype(str).str.contains(search_pattern, regex=True, na=False)]

raw_tail_numbers = filtered_fleet['Tail Number (등록기호)'].unique()
tail_numbers = sorted([str(t) for t in raw_tail_numbers if str(t).lower() != 'nan'])

if len(tail_numbers) == 0:
    st.warning("데이터베이스에 선택하신 기종에 해당하는 Tail Number가 없습니다.")
    st.stop()

selected_tail = st.sidebar.selectbox("Tail Number 선택", tail_numbers)

# 6. [강화됨] FSN 매칭 및 전처리 로직
raw_fsn = filtered_fleet[filtered_fleet['Tail Number (등록기호)'].astype(str) == selected_tail]['FSN'].values[0]

# 구글 시트에서 54로 입력되거나 파이썬이 54.0으로 읽더라도 무조건 Airbus 규격인 '054'로 완벽하게 변환
try:
    fsn_value = str(int(float(raw_fsn))).zfill(3)
except:
    fsn_value = str(raw_fsn).strip()

st.sidebar.info(f"✈️ 선택된 호기 FSN: **{fsn_value}**")

# Dispatch DB 로드 및 필터링
filtered_db_by_model = db_df[db_df['기종 (Model)'].astype(str).str.contains(search_pattern, regex=True, na=False)]
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
