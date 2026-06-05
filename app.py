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

@st.cache_data(ttl=0) # 항상 최신 데이터 로드
def load_data():
    db = pd.read_csv('Quick Dispatch - Quick Dispatch_DB.csv')
    fleet = pd.read_csv('Quick Dispatch - Fleet Mapping DB.csv')
    fleet['Tail Number (등록기호)'] = fleet['Tail Number (등록기호)'].apply(clean_tail_number)
    return db, fleet

db_df, fleet_df = load_data()

# 3. URL 자동 생성 함수 (공통 검색)
def get_search_url(task_str):
    clean_id = re.sub(r'[^0-9-]', '', str(task_str))
    return f"https://w3.airbus.com/1T40/search?q={clean_id}"

# 3-1. A321 전용 Maximize URL (룰 추출 및 FSN 소트 적용)
def generate_a321_maximize_url(task_str, msn_str="", fsn_str=""):
    clean_task = re.sub(r'[^0-9]', '', str(task_str))
    if len(clean_task) < 12: return None
        
    task_12 = clean_task[:12]
    task_prefix = task_12[:6]
    
    # 룰 1: 엔진(ATA 70 이상)은 04M, 그 외 기체 계통은 040 노드 적용
    if int(task_prefix[:2]) >= 70:
        node_id = "04M"
    else:
        node_id = "040"
        
    revision_id = "773433_SGML_C"
    item_id = f"{revision_id}_EN{task_12}00"
    parent_id = f"{revision_id}_EN{task_prefix}{node_id}" 
    
    wc_params = []
    
    # 룰 2: FSN 소트 강제 삽입 (요청 사항)
    if fsn_str and str(fsn_str).upper() != 'NAN':
        wc_params.append(f"FSN:{fsn_str}")
        
    # 룰 3: 추출된 패밀리 코드 및 doctype:AMM 유지
    wc_params.append("actype:A318;actype:A319;actype:A320;actype:A321;customization:AAR;doctype:AMM")
    
    # 룰 4: 추출된 기번(Tail Number) N + MSN 소트
    if msn_str and str(msn_str).upper() != 'NAN':
        try:
            msn_clean = str(int(float(msn_str)))
            wc_params.append(f"tailNumber:N{msn_clean}")
        except:
            pass
            
    wc_final = ";".join(wc_params)
    
    # 룰 5: context=document 복구 적용
    return f"https://w3.airbus.com/1T40/maximize?itemId={item_id}&parentId={parent_id}&itemType=DATAMODULE&itemFormat=HTML&revisionItemId={revision_id}&context=document&wc={wc_final}&viewMinimize=true"

# 3-2. A330 전용 Maximize URL
def generate_a330_maximize_url(task_str, msn_str=""):
    clean_task = re.sub(r'[^0-9]', '', str(task_str))
    if len(clean_task) < 12: return None
        
    task_12 = clean_task[:12]
    revision_id = "768908_SGML_C"
    item_id = f"{revision_id}_EN{task_12}00"
    parent_id = f"{revision_id}_EN{task_12}" 
    
    msn_clean = re.sub(r'[^0-9]', '', str(msn_str)) if msn_str and str(msn_str).upper() != 'NAN' else "ERROR"
    wc_final = f"actype:A330;customization:AAR;tailNumber:F{msn_clean}"
    
    return f"https://w3.airbus.com/1T40/maximize?itemId={item_id}&parentId={parent_id}&itemType=DATAMODULE&itemFormat=HTML&revisionItemId={revision_id}&wc={wc_final}&context=dataModule&viewMinimize=true"

# 3-3. A350 전용 URL
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

# 3-4. A380 전용 Maximize URL
def generate_a380_maximize_url(task_str, msn_str=""):
    clean_task = re.sub(r'[^0-9]', '', str(task_str))
    if len(clean_task) < 12: return None
        
    task_12 = clean_task[:12]
    revision_id = "763497_SGML_C"
    item_id = f"{revision_id}_EN{task_12}00"
    parent_id = f"{revision_id}_EN{task_12}" 
    
    msn_clean = re.sub(r'[^0-9]', '', str(msn_str)) if msn_str and str(msn_str).upper() != 'NAN' else "ERROR"
    wc_final = f"FSN:005;actype:A380;customization:AAR;tailNumber:L{msn_clean}"
    
    return f"https://w3.airbus.com/1T40/maximize?itemId={item_id}&parentId={parent_id}&itemType=DATAMODULE&itemFormat=HTML&revisionItemId={revision_id}&wc={wc_final}&context=dataModule&viewMinimize=true"


# 4. 사이드바 필터 설정
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

# Fleet DB에서 기종에 맞는 Tail Number 목록 로드
filtered_fleet = fleet_df[fleet_df['A/C Model'].astype(str).str.contains(search_pattern, regex=True, na=False)]
raw_tail_numbers = filtered_fleet['Tail Number (등록기호)'].unique()
tail_numbers = sorted([str(t) for t in raw_tail_numbers if str(t).lower() != 'nan'])

if len(tail_numbers) == 0:
    st.warning("데이터베이스에 선택하신 기종에 해당하는 Tail Number가 없습니다.")
    st.stop()

selected_tail = st.sidebar.selectbox("Tail Number 선택", tail_numbers)

# 5. Fleet Mapping DB 정보 파싱
tail_data_row = filtered_fleet[filtered_fleet['Tail Number (등록기호)'].astype(str) == selected_tail].iloc[0]
db_model_str = str(tail_data_row.get('A/C Model', '')).upper()

fsn_value = ""
fsn_cols = [col for col in tail_data_row.index if 'FSN' in str(col).upper()]
if fsn_cols:
    raw_fsn = tail_data_row[fsn_cols[0]]
    if pd.notna(raw_fsn) and str(raw_fsn).strip().upper() != 'NAN':
        fsn_value = re.sub(r'[^0-9]', '', str(raw_fsn)).zfill(3)

msn_value = ""
msn_cols = [col for col in tail_data_row.index if 'MSN' in str(col).upper()]
if msn_cols:
    raw_msn = tail_data_row[msn_cols[0]]
    if pd.notna(raw_msn) and str(raw_msn).strip().upper() != 'NAN':
        msn_value = re.sub(r'[^0-9]', '', str(raw_msn))

if not msn_value:
    st.sidebar.error("⚠️ Fleet DB에 MSN 데이터가 누락되었습니다.")
else:
    st.sidebar.info(f"✈️ Fleet DB 식별 정보\n**Model:** {db_model_str}\n**MSN:** {msn_value} | **FSN:** {fsn_value}")

# 6. 기본 DB 기종 필터링
filtered_db_by_model = db_df[db_df['기종 (Model)'].astype(str).str.contains(search_pattern, regex=True, na=False)].copy()

# 7. 독립적인 콤보박스 (종속 제한 없이 모두 전체 리스트 표기)
if '항목 (Section)' in filtered_db_by_model.columns and not filtered_db_by_model.empty:
    
    sections_options = ['전체 (All)'] + filtered_db_by_model['항목 (Section)'].unique().tolist()
    
    def extract_ata_prefix(ref_str):
        match = re.search(r'(\d{2}-\d{2})', str(ref_str))
        return match.group(1) if match else "미분류"
        
    filtered_db_by_model['ATA_Prefix'] = filtered_db_by_model['링크 (Reference)'].apply(extract_ata_prefix)
    ata_options = sorted([ata for ata in filtered_db_by_model['ATA_Prefix'].unique() if ata != "미분류"])
    
    if '작업 (Task Description)' in filtered_db_by_model.columns:
        task_options = filtered_db_by_model['작업 (Task Description)'].unique().tolist()
    else:
        task_options = []

    selected_section = st.sidebar.selectbox("항목 (Section) 선택", sections_options)
    selected_ata = st.sidebar.selectbox("세부 챕터 (ATA) 선택", ['전체 (All)'] + ata_options)
    
    if task_options:
        selected_task = st.sidebar.selectbox("작업 (Task Description) 선택", ['전체 (All)'] + task_options)
    else:
        selected_task = '전체 (All)'

    final_filtered_db = filtered_db_by_model.copy()
    
    if selected_section != '전체 (All)':
        final_filtered_db = final_filtered_db[final_filtered_db['항목 (Section)'] == selected_section]
        
    if selected_ata != '전체 (All)':
        final_filtered_db = final_filtered_db[final_filtered_db['ATA_Prefix'] == selected_ata]
        
    if selected_task != '전체 (All)':
        final_filtered_db = final_filtered_db[final_filtered_db['작업 (Task Description)'] == selected_task]

else:
    final_filtered_db = filtered_db_by_model

# 8. 메인 화면 리스트 출력
st.subheader(f"작업 리스트: {selected_tail}")

if final_filtered_db.empty:
    st.warning("선택하신 조합에 부합하는 작업 데이터가 없습니다.")
else:
    for _, row in final_filtered_db.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**[{row['항목 (Section)']}]** {row['작업 (Task Description)']}")
                st.caption(f"Ref: {row['링크 (Reference)']}")
            with col2:
                max_url = None
                if '321' in db_model_str or '320' in db_model_str or '319' in db_model_str or '318' in db_model_str:
                    # A321의 경우 fsn_value 인자를 함께 넘겨 룰 반영
                    max_url = generate_a321_maximize_url(row['링크 (Reference)'], msn_value, fsn_value)
                elif '330' in db_model_str:
                    max_url = generate_a330_maximize_url(row['링크 (Reference)'], msn_value)
                elif '350' in db_model_str:
                    max_url = generate_a350_url(row['링크 (Reference)'], msn_value)
                elif '380' in db_model_str:
                    max_url = generate_a380_maximize_url(row['링크 (Reference)'], msn_value)
                
                if max_url:
                    st.link_button("바로가기 (Maximize)", max_url, type="primary")
                
                search_url = get_search_url(row['링크 (Reference)'])
                st.link_button("검색으로 열기 (Search)", search_url)

# 9. 데이터 전체 검색
st.markdown("---")
st.subheader("데이터베이스 전체 검색")
search_query = st.text_input("검색어를 입력하세요 (예: Door, Leak 등)")
if search_query:
    result = final_filtered_db[final_filtered_db['작업 (Task Description)'].str.contains(search_query, case=False, na=False)]
    st.dataframe(result, use_container_width=True)
