import streamlit as st
import time
from datetime import datetime
from dotenv import load_dotenv

from core.database import init_db, PostgresDB, upsert_character, set_app_setting, get_app_setting, reset_db
from core.loa_api import LostArkAPI
from ui.todo_list import render_todo_list 
from core.reset_manager import check_and_reset_tasks

# [1] 프로그램 시작 전 환경변수 로드 (가장 먼저!)
load_dotenv()

# [2] 페이지 기본 설정
st.set_page_config(
    page_title="LOA AGENT v2", 
    page_icon="🛡️",
    layout="wide", # 화면 넓게 쓰기
    initial_sidebar_state="expanded"
)

# 👇 [NEW] 앱 시작하자마자 리셋 검사 실행! 👇
if 'reset_checked' not in st.session_state:
    init_db() # DB 테이블 없으면 생성
    msgs = check_and_reset_tasks()
    if msgs:
        # 리셋된 게 있으면 화면 우측 하단에 알림(Toast) 띄우기
        for msg in msgs:
            st.toast(msg, icon="🔄")
    st.session_state['reset_checked'] = True

# --- [스타일 정의] ---
st.markdown("""
<style>
    .char-card-header { display: flex; align-items: baseline; gap: 8px; margin-bottom: 0px !important; padding-bottom: 0px !important; color: #333; }
    .char-name { font-size: 18px; font-weight: 800; color: #000; }
    .char-details { font-size: 14px; font-weight: 400; color: #666; }
    hr.half-margin { margin-top: 8px !important; margin-bottom: 8px !important; border-color: #eee; }
    .economy-container { display: flex; flex-direction: column; align-items: flex-end; justify-content: center; height: 100%; }
    .economy-label { font-size: 12px; color: #888; margin-bottom: 2px; }
    .economy-value { font-size: 18px; font-weight: 800; color: #333; line-height: 1.2; }
    input::-webkit-outer-spin-button, input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
    input[type=number] { -moz-appearance: textfield; }
</style>
""", unsafe_allow_html=True)

# --- [사이드바] 관리자 도구 ---
with st.sidebar:
    
    # 1. API 키 확인
    api = LostArkAPI()
    if api.api_key:
        st.success("API 연결됨 ✅")
    else:
        st.error("API 키가 없습니다. .env 확인")

    # 2. [요구사항 1, 1.1] 대표 캐릭터 이름 입력 (멀티 지원)
    st.markdown("### 대표 캐릭터 설정")
    st.caption("여러 계정이면 쉼표(,)로 구분해서 입력하세요.")
    
    # DB나 세션에서 마지막 입력값 불러오기 (여기선 간단히 세션)
    default_name = st.session_state.get('main_char_name', '')
    main_char_input = st.text_input("닉네임 입력", value=default_name, placeholder="예: 본캐1, 본캐2")

    # 3. [요구사항 4] 목표 날짜 설정 (골드 너프일)
    st.markdown("### 목표 날짜 (골드 계산)")
    saved_date = get_app_setting("target_date")
    target_date_input = st.date_input(
        "너프/목표 예상일", 
        value=datetime.strptime(saved_date, "%Y-%m-%d").date() if saved_date else datetime.now().date()
    )
    
    # 날짜가 바뀌면 DB 저장
    if str(target_date_input) != saved_date:
        set_app_setting("target_date", str(target_date_input))
        st.toast("목표 날짜가 저장되었습니다.", icon="💾")

    st.divider()

    # 4. 동기화 버튼 (DB 초기화 옵션 통합)
    force_reset = st.checkbox("기존 데이터 날리고 새로 받기", help="체크하면 현재 저장된 모든 숙제 기록이 초기화됩니다.")
    
    if st.button("원정대 동기화 시작", use_container_width=True):
        if not main_char_input:
            st.warning("닉네임을 입력해주세요.")
        else:
            st.session_state['main_char_name'] = main_char_input
            
            # [수정됨] 체크박스 켜져 있으면 'reset_db()' 실행
            if force_reset:
                reset_db()  # <-- 여기! 진짜로 삭제하는 함수 호출
                st.toast("DB가 완전히 초기화되었습니다.", icon="🧹")  

            # [핵심] 콤마로 구분된 닉네임들을 순회하며 동기화
            names = [n.strip() for n in main_char_input.split(',')]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_steps = len(names)
            
            try:
                for i, name in enumerate(names):
                    if not name: continue
                    status_text.text(f"📡 '{name}' 원정대 검색 중...")
                    
                    # 1. API 호출
                    char_list = api.get_characters(name)
                    if not char_list:
                        st.error(f"'{name}' 캐릭터를 찾을 수 없습니다.")
                        continue
                        
                    # 2. DB 저장 (전투력 보정 포함)
                    for char in char_list:
                        upsert_character(char)
                    
                    progress_bar.progress((i + 1) / total_steps)
                
                st.success("✅ 모든 동기화 완료!")
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"오류 발생: {e}")


# =========================================================
# 🏠 메인 화면
# =========================================================
st.title("🛡️ LOA AGENT v2")

# 탭 뷰
tab1, tab2 = st.tabs(["📝 숙제 체크리스트", "원정대 경영 지표"])

with tab1:
    render_todo_list()

with tab2:
    # (다음 단계에서 구현할 통계 대시보드 자리)
    st.info("경영 지표 대시보드는 다음 업데이트에 추가됩니다!")