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
    /* 버튼 상하 간격 조절 */
    div.stButton > button {
        margin-bottom: 5px;
    }
    </style>
    <div class="responsive-title">✈️ Airbus Quick Dispatch Guide</div>
    """,
    unsafe_allow_html=True
)

# 2. 데이터 로드 (캐시 제거 - 항상 최신 데이터를 읽어옴)
def load_data():
    db = pd.read_csv('Quick Dispatch - Quick Dispatch_DB.csv')
    fleet = pd.read_csv('Quick Dispatch - Fleet Mapping DB.csv')
    return db, fleet

db_df, fleet_df = load_data()

# 3. URL 자동 생성 함수 (기존 검색 방식)
def get_search_url(task_str):
    clean_id = re.sub(r'[^0-9-]', '', str(task_str))
    return f"https://w3.airbus.com/1T40/search?q={clean_id}"

# 3-1. A321 전용 Maximize URL 생성 함수
def generate_a321_maximize_url(task_str, fsn_str="", msn_str=""):
    clean_task = re.sub(r'[^0-9]', '', str(task_str))
    if len(clean_task) < 12: 
        return None
        
    task_12 = clean_task[:12]
    task_prefix = task_12[:6]
    
    revision_id = "773433_SGML_C"
    item_id = f"{revision_id}_EN{task_12}00"
    parent_id = f"{revision_id}_EN{task_prefix}020"
    
    wc_base = "actype:A318;actype:A319;actype:A320;actype:A321;customization:AAR;doctype:AMM"
    wc_params = []
    
    if fsn_str and str(fsn_str).upper() != 'NAN':
        wc_params.append(f"FSN:{fsn_str}")
        
    wc_params.append(wc_base)
    
    if msn_str and str(msn_str).upper() != 'NAN':
        wc_params.append(f"tailNumber:N{msn_str}")
        
    wc_final = ";".join(wc_params)
    
    url = (
        f"https://w3.airbus.com/1T40/maximize"
        f"?itemId={item_id}"
        f"&parentId={parent_id}"
        f"&itemType=DATAMODULE"
        f"&itemFormat=HTML"
        f"&revisionItemId={revision_id}"
        f"&context=document"
        f"&wc={wc_final}"
        f"&viewMinimize=true"
    )
    return url

# 3-2. A330 전용 Maximize URL 생성 함수
def generate_a330_maximize_url(task_str, fsn_str="", msn_str=""):
    clean_task = re.sub(r'[^0-9]', '', str(task_str))
    if len(clean_task) < 12: 
        return None
        
    task_12 = clean_task[:12]
    task_prefix = task_12[:6]
    
    revision_id = "768908_SGML_C"
    item_id = f"{revision_id}_EN{task_12}00"
    parent_id = f"{revision_id}_EN{task_prefix}040" # A330 룰 적용
    
    wc_params = ["actype:A330", "customization:AAR", "doctype:AMM"]
    
    if msn_str and str(msn_str).upper() != 'NAN':
        try:
            clean_msn = int(float(msn_str)) 
            wc_params.append(f"tailNumber:F{clean_msn}")
        except:
            pass
            
    wc_final = ";".join(wc_params)
    
    url = (
        f"https://w3.airbus.com/1T40/maximize"
        f"?itemId={item_id}"
        f"&parentId={parent_id}"
        f"&itemType=DATAMODULE"
        f"&itemFormat=HTML"
        f"&revisionItemId={revision_id}"
        f"&context=document"
        f"&wc={wc_final}"
        f"&viewMinimize=true"
    )
    return url

# 4. FSN 적용 여부 확인 함수 (정밀 필터링)
def check_effectivity(fsn_str, eff_str):
    if pd.isna(eff_str): return True 
    eff_str = str(eff_str).upper()
    if 'ALL' in eff_str: return True 
    
    if not fsn_str or fsn_str == 'NAN': return True 
    
    ranges = re.findall(r'(\d+)\s*-\s*(\d+)', eff_str)
    singles = re.findall(r'\b(\d+)\b', eff_str)
    
    try:
        fsn_int = int(fsn_str)
        for start, end in ranges:
            if int(start) <= fsn_int <= int(end):
                return True
        for s in singles:
            if int(s) == fsn_int:
                return True
    except ValueError:
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

# 6. FSN 및 MSN 매칭 및 전처리 로직
tail_data = filtered_fleet[filtered_fleet['Tail Number (등록기호)'].astype(str) == selected_tail]
raw_fsn = tail_data['FSN'].values[0]

try:
    fsn_value = str(int(float(raw_fsn))).zfill(3)
except:
    fsn_value = str(raw_fsn).strip()

msn_value = ""
if 'MSN' in tail_data.columns:
    raw_msn = tail_data['MSN'].values[0]
    try:
        msn_value = str(int(float(raw_msn)))
    except:
        msn_value = str(raw_msn).strip()

if msn_value:
    st.sidebar.info(f"✈️ 선택된 호기\nFSN: **{fsn_value}** | MSN: **{msn_value}**")
else:
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
st.subheader(f"작업 리스트: {selected_tail}")

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
                # 기종별 맞춤형 다이렉트 버튼 출력 로직
                if 'A321' in selected_display:
                    max_url = generate_a321_maximize_url(row['링크 (Reference)'], fsn_value, msn_value)
                    if max_url:
                        st.link_button("바로가기 (Maximize)", max_url, type="primary")
                elif 'A330' in selected_display:
                    max_url = generate_a330_maximize_url(row['링크 (Reference)'], fsn_value, msn_value)
                    if max_url:
                        st.link_button("바로가기 (Maximize)", max_url, type="primary")
                
                # 항상 기본으로 나타나는 검색 방식 버튼
                search_url = get_search_url(row['링크 (Reference)'])
                st.link_button("검색으로 열기 (Search)", search_url)

# 9. 데이터 전체 검색 기능
st.markdown("---")
st.subheader("데이터베이스 전체 검색")
search_query = st.text_input("검색어를 입력하세요 (예: Door, Leak 등)")
if search_query:
    result = final_filtered_db[final_filtered_db['작업 (Task Description)'].str.contains(search_query, case=False, na=False)]
    st.dataframe(result, use_container_width=True)
