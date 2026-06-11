import streamlit as st
import pandas as pd
import re

# 1. 페이지 설정
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
    div.stButton > button { margin-bottom: 5px; }
    </style>
    <div class="responsive-title">✈️ Airbus Quick Dispatch Guide</div>
    """,
    unsafe_allow_html=True
)

# 2. 데이터 정제 및 로드
def clean_tail_number(val):
    match = re.search(r'(HL\d{4})', str(val))
    return match.group(1) if match else str(val)

@st.cache_data(ttl=0)
def load_data():
    db = pd.read_csv('Quick Dispatch - Quick Dispatch_DB.csv')
    fleet = pd.read_csv('Quick Dispatch - Fleet Mapping DB.csv')
    fleet['Tail Number (등록기호)'] = fleet['Tail Number (등록기호)'].apply(clean_tail_number)
    return db, fleet

db_df, fleet_df = load_data()

# 3. URL 자동 생성 함수
def get_search_url(task_str):
    clean_id = re.sub(r'[^0-9-]', '', str(task_str))
    return f"https://w3.airbus.com/1T40/search?q={clean_id}"

def generate_a321_maximize_url(task_str, msn_str=""):
    clean_task = re.sub(r'[^0-9]', '', str(task_str))
    if len(clean_task) < 12: return None
    task_12 = clean_task[:12]
    msn_clean = re.sub(r'[^0-9]', '', str(msn_str)) if msn_str and str(msn_str).upper() != 'NAN' else "ERROR"
    rev_id = "773433_SGML_C"
    
    url = (
        f"https://w3.airbus.com/1T40/maximize?"
        f"itemId={rev_id}_EN{task_12}00"
        f"&parentId={rev_id}_EN{task_12}"
        f"&itemType=DATAMODULE"
        f"&itemFormat=HTML"
        f"&revisionItemId={rev_id}"
        f"&wc=actype:A318;actype:A319;actype:A320;actype:A321;customization:AAR;tailNumber:N{msn_clean}"
        f"&context=dataModule"
        f"&viewMinimize=true"
    )
    return url

def generate_a330_maximize_url(task_str, msn_str=""):
    clean_task = re.sub(r'[^0-9]', '', str(task_str))
    if len(clean_task) < 12: return None
    task_12 = clean_task[:12]
    revision_id = "768908_SGML_C"
    msn_clean = re.sub(r'[^0-9]', '', str(msn_str)) if msn_str and str(msn_str).upper() != 'NAN' else "ERROR"
    wc_final = f"actype:A330;customization:AAR;tailNumber:F{msn_clean}"
    
    return f"https://w3.airbus.com/1T40/maximize?itemId={revision_id}_EN{task_12}00&parentId={revision_id}_EN{task_12}&itemType=DATAMODULE&itemFormat=HTML&revisionItemId={revision_id}&wc={wc_final}&context=dataModule&viewMinimize=true"

def generate_a350_url(task_str, msn_str=""):
    task = re.sub(r'^(TASK|Ref\.\s+MP)\s+', '', str(task_str).strip(), flags=re.IGNORECASE)
    rev = "776735_S1KD_C"
    msn_clean = re.sub(r'[^0-9]', '', str(msn_str)) if msn_str and str(msn_str).upper() != 'NAN' else "ERROR"
    wc_final = f"actype:A350;customization:AAR;tailNumber:P{msn_clean}"
    
    if 'XX' in task:
        match = re.search(r'-([0-9X]{2})-([0-9X]{2})-([0-9X]{2})-', task)
        a1, a2, a3 = match.groups() if match else ('', '', '')
        ata_fmt = f"{a1 if a1!='XX' else ''}_{a2[0] if a2!='XX' else ''}_{a2[1] if a2!='XX' else ''}_{a3 if a3!='XX' else ''}"
        return f"https://w3.airbus.com/1T40/document/{rev}/toc?itemId=MAINTENANCE%20PROCEDURE&parentId={rev}_{ata_fmt}&itemType=BUSINESS_CATEGORY&wc={wc_final}"
    else:
        return f"https://w3.airbus.com/1T40/maximize?itemId={rev}_{task}&parentId={rev}_{task}&itemType=DATAMODULE&itemFormat=HTML&revisionItemId={rev}&wc={wc_final}&context=dataModule&viewMinimize=true"

def generate_a380_maximize_url(task_str, msn_str=""):
    clean_task = re.sub(r'[^0-9]', '', str(task_str))
    if len(clean_task) < 12: return None
    task_12 = clean_task[:12]
    revision_id = "763497_SGML_C"
    msn_clean = re.sub(r'[^0-9]', '', str(msn_str)) if msn_str and str(msn_str).upper() != 'NAN' else "ERROR"
    wc_final = f"FSN:005;actype:A380;customization:AAR;tailNumber:L{msn_clean}"
    
    return f"https://w3.airbus.com/1T40/maximize?itemId={revision_id}_EN{task_12}00&parentId={revision_id}_EN{task_12}&itemType=DATAMODULE&itemFormat=HTML&revisionItemId={revision_id}&wc={wc_final}&context=dataModule&viewMinimize=true"


# 4. 사이드바 필터 설정 (종속형)
st.sidebar.header("필터 설정")

# (1) Base Model 선택 (기본값: 전체)
display_models = ['전체 (All)', 'A321 (318/319/320 포함)', 'A330', 'A350', 'A380']
selected_display = st.sidebar.selectbox("기종 그룹 (Base Model)", display_models, index=0)

search_pattern = ""
if 'A321' in selected_display: search_pattern = '318|319|320|321'
elif 'A330' in selected_display: search_pattern = '330'
elif 'A350' in selected_display: search_pattern = '350'
elif 'A380' in selected_display: search_pattern = '380'

# (2) Fleet DB 필터링 및 Tail Number 선택
if search_pattern:
    filtered_fleet = fleet_df[fleet_df['A/C Model'].astype(str).str.contains(search_pattern, regex=True, na=False)]
else:
    filtered_fleet = fleet_df

raw_tail_numbers = filtered_fleet['Tail Number (등록기호)'].unique()
tail_numbers = ['전체 (All)'] + sorted([str(t) for t in raw_tail_numbers if str(t).lower() != 'nan'])

selected_tail = st.sidebar.selectbox("Tail Number 선택", tail_numbers, index=0)

# (3) MSN/FSN 추출
msn_value = ""
if selected_tail != '전체 (All)':
    tail_data_row = filtered_fleet[filtered_fleet['Tail Number (등록기호)'].astype(str) == selected_tail].iloc[0]
    db_model_str = str(tail_data_row.get('A/C Model', '')).upper()
    
    fsn_cols = [col for col in tail_data_row.index if 'FSN' in str(col).upper()]
    fsn_value = re.sub(r'[^0-9]', '', str(tail_data_row[fsn_cols[0]])).zfill(3) if fsn_cols and pd.notna(tail_data_row[fsn_cols[0]]) else ""
    
    msn_cols = [col for col in tail_data_row.index if 'MSN' in str(col).upper()]
    msn_value = re.sub(r'[^0-9]', '', str(tail_data_row[msn_cols[0]])) if msn_cols and pd.notna(tail_data_row[msn_cols[0]]) else ""

    st.sidebar.info(f"✈️ Fleet 식별 정보\n**Model:** {db_model_str}\n**MSN:** {msn_value} | **FSN:** {fsn_value}")
else:
    st.sidebar.info("ℹ️ 전체 모드입니다. 기번을 선택하시면 기체 맞춤 URL이 생성됩니다.")

# 5. DB 필터링 및 하위 콤보박스 종속 (Cascading) 로직
if search_pattern:
    filtered_db = db_df[db_df['기종 (Model)'].astype(str).str.contains(search_pattern, regex=True, na=False)].copy()
else:
    filtered_db = db_df.copy()

# ATA Prefix 세팅
def extract_ata_prefix(ref_str):
    match = re.search(r'(\d{2}-\d{2})', str(ref_str))
    return match.group(1) if match else "미분류"
filtered_db['ATA_Prefix'] = filtered_db['링크 (Reference)'].apply(extract_ata_prefix)

# [범위 한정 1] 항목 (Section)
if '항목 (Section)' in filtered_db.columns:
    sections_options = ['전체 (All)'] + filtered_db['항목 (Section)'].dropna().unique().tolist()
    selected_section = st.sidebar.selectbox("항목 (Section) 선택", sections_options, index=0)
    if selected_section != '전체 (All)':
        filtered_db = filtered_db[filtered_db['항목 (Section)'] == selected_section]

# [범위 한정 2] 세부 챕터 (ATA) -> 상위 Section 결과에만 의존하여 옵션 표시
ata_options = sorted([ata for ata in filtered_db['ATA_Prefix'].unique() if ata != "미분류"])
selected_ata = st.sidebar.selectbox("세부 챕터 (ATA) 선택", ['전체 (All)'] + ata_options, index=0)
if selected_ata != '전체 (All)':
    filtered_db = filtered_db[filtered_db['ATA_Prefix'] == selected_ata]

# [범위 한정 3] 작업 (Task Description) -> 상위 ATA 결과에만 의존하여 옵션 표시
if '작업 (Task Description)' in filtered_db.columns:
    task_options = filtered_db['작업 (Task Description)'].dropna().unique().tolist()
    selected_task = st.sidebar.radio("작업 (Task Description) 선택", ['전체 (All)'] + task_options, index=0)
    if selected_task != '전체 (All)':
        filtered_db = filtered_db[filtered_db['작업 (Task Description)'] == selected_task]

# ==========================================
# ★ 6. 전체 1차 & 2차 키워드 텍스트 검색 
# ==========================================
st.markdown("---")
st.subheader("🔍 키워드 다중 검색")

# 검색창을 가로로 두 개 나란히 배치합니다.
col_search1, col_search2 = st.columns(2)

with col_search1:
    search_1 = st.text_input("1차 검색어 (예: Door, Pump 등)")
with col_search2:
    search_2 = st.text_input("2차 검색어 (1차 결과 내 추가 검색, 예: Leak)")

# 1차 검색어가 입력되면 해당 단어로 필터링
if search_1:
    filtered_db = filtered_db[filtered_db['작업 (Task Description)'].astype(str).str.contains(search_1, case=False, na=False)]

# 2차 검색어가 입력되면 1차로 걸러진 상태에서 한 번 더 필터링
if search_2:
    filtered_db = filtered_db[filtered_db['작업 (Task Description)'].astype(str).str.contains(search_2, case=False, na=False)]


# ==========================================
# 7. 메인 화면 리스트 출력
# ==========================================
st.markdown("---")
title_text = f"작업 리스트: {selected_tail}" if selected_tail != '전체 (All)' else "작업 리스트: 전체 보기"

# 필터링 결과 몇 건인지 표시
st.subheader(f"{title_text} (총 {len(filtered_db)}건)")

if filtered_db.empty:
    st.warning("선택하신 조합이나 검색어에 부합하는 작업 데이터가 없습니다.")
else:
    for _, row in filtered_db.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**[{row.get('항목 (Section)', '미분류')}]** {row.get('작업 (Task Description)', '내용 없음')}")
                st.caption(f"Ref: {row.get('링크 (Reference)', '')}")
            with col2:
                max_url = None
                
                # 기종 구분이 전체일 경우 각 데이터 행의 기종을 추적하여 URL 부여
                row_model = str(row.get('기종 (Model)', '')).upper()
                model_indicator = row_model if row_model else selected_display
                
                if '321' in model_indicator or '320' in model_indicator or '319' in model_indicator or '318' in model_indicator:
                    max_url = generate_a321_maximize_url(row['링크 (Reference)'], msn_value)
                elif '330' in model_indicator:
                    max_url = generate_a330_maximize_url(row['링크 (Reference)'], msn_value)
                elif '350' in model_indicator:
                    max_url = generate_a350_url(row['링크 (Reference)'], msn_value)
                elif '380' in model_indicator:
                    max_url = generate_a380_maximize_url(row['링크 (Reference)'], msn_value)
                
                if max_url:
                    st.link_button("바로가기 (Maximize)", max_url, type="primary")
                
                search_url = get_search_url(row['링크 (Reference)'])
                st.link_button("검색으로 열기 (Search)", search_url)
