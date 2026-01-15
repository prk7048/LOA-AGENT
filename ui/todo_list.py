import streamlit as st
from datetime import datetime
from core.database import (
    PostgresDB, update_memo, update_spent_gold, 
    get_app_setting, get_expedition_tasks, add_expedition_task, 
    delete_expedition_task, update_expedition_task_check
)

def render_todo_list():
    """숙제 리스트 렌더링 메인 함수"""
    
    # ---------------------------------------------------------
    # 1. 💰 목표 달성 계산기 (Goal Calculator)
    # ---------------------------------------------------------
    # DB에서 목표 날짜 가져오기
    target_date_str = get_app_setting("target_date")
    if not target_date_str:
        target_date_str = datetime.now().strftime("%Y-%m-%d")
    
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    
    # 남은 기간 계산 (수요일 기준 리셋 횟수 계산이 정확하지만, 일단 단순 주 단위 계산)
    days_left = (target_date - today).days
    weeks_left = max(0, days_left // 7)
    
    # 주간 총 예상 수익 계산 (DB에서 전체 긁어오기)
    weekly_total_income = 0
    try:
        with PostgresDB() as cur:
            cur.execute("SELECT gold_reward, total_count FROM todos WHERE category = '주간'")
            rows = cur.fetchall()
            for r in rows:
                weekly_total_income += (r['gold_reward'] * r['total_count'])
    except:
        weekly_total_income = 0
        
    projected_income = weekly_total_income * weeks_left

    # 상단 배너 출력
    st.info(f"""
     **목표일({target_date})까지 남은 시간: {weeks_left}주 ({days_left}일)**
    \n 주간 원정대 수익: **{weekly_total_income:,} G**  
    \n 목표일까지 예상 수익: **{projected_income:,} G**
    """)

    st.write("") 

    # ---------------------------------------------------------
    # 2. 🏰 원정대 통합 숙제 (Customizable)
    # ---------------------------------------------------------
    with st.container(border=True):
        c_head, c_btn = st.columns([8, 2])
        with c_head:
            st.markdown("### 원정대 통합 숙제")
        with c_btn:
            with st.expander("관리 ⚙️"):
                # 1. 숙제 이름 입력
                new_task = st.text_input("숙제 이름", placeholder="예: 카게")
                
                # 2. [NEW] 리셋 주기 선택
                # UI 편의를 위해 한글로 보여주고, 실제 값은 영어로 매핑
                cycle_options = {"매주 (수요일 6시)": "WEEKLY", "매일 (오전 6시)": "DAILY", "N일 간격": "INTERVAL"}
                selected_label = st.selectbox("리셋 주기", list(cycle_options.keys()))
                reset_type = cycle_options[selected_label]
                
                reset_value = 1
                if reset_type == "INTERVAL":
                    reset_value = st.number_input("며칠마다?", min_value=1, value=2, help="예: 2를 입력하면 2일 뒤에 초기화됩니다.")
                
                if st.button("추가", key="add_exp_btn"):
                    if new_task:
                        add_expedition_task(new_task, reset_type, reset_value)
                        st.rerun()
                        
                st.divider()

    st.write("") 

    # ---------------------------------------------------------
    # 3. 탭 및 캐릭터 카드 (기존 로직 유지)
    # ---------------------------------------------------------
    sub_tab_weekly, sub_tab_daily = st.tabs(["주간 숙제", "일일 숙제"])

    try:
        with PostgresDB() as cur:
            # 전투력 높은 순 정렬 (요구사항 5번 이미 적용됨 - DB Upsert 시점이 아닌 조회 시점 정렬 필요)
            # 하지만 loa_api에서 이미 combat_power를 업데이트 해줬고, upsert에서 저장함.
            # 여기서 불러올 때 ORDER BY combat_power DESC 하면 됨.
            cur.execute("SELECT * FROM characters ORDER BY combat_power DESC") 
            characters = cur.fetchall()

            cur.execute("SELECT * FROM todos ORDER BY id ASC")
            all_todos = cur.fetchall()
            
    except Exception as e:
        st.error(f"데이터 로딩 실패: {e}")
        return

    with sub_tab_weekly:
        _render_character_cards(characters, all_todos, "WEEKLY")
    with sub_tab_daily:
        _render_character_cards(characters, all_todos, "DAILY")


def _render_character_cards(characters, all_todos, target_tab):
    """캐릭터 카드 렌더링 (수익 계산 수정본 유지)"""
    cols = st.columns(4)
    
    for idx, char in enumerate(characters):
        char_name = char['character_name']
        
        with cols[idx % 4]:
            with st.container(border=True):
                # A. 헤더
                st.markdown(f"""
                    <div class="char-card-header">
                        <span class="char-name">{char_name}</span>
                        <span class="char-details">
                            {char['character_class']} | 
                            Lv.{char['item_avg_level']:.2f} | 
                            🗡️{char['combat_power']:,}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("<hr class='half-margin'>", unsafe_allow_html=True)

                # B. 수익 계산 및 숙제 필터링
                my_tasks = [t for t in all_todos if t['character_name'] == char_name]
                weekly_tasks = [t for t in my_tasks if t['category'] == '주간']
                # 주간 총 수익 계산 (탭 상관없이 고정)
                total_income = sum(t['gold_reward'] for t in weekly_tasks)

                if target_tab == "WEEKLY":
                    st.checkbox("길드 상점 / 혈석 교환", key=f"guild_{char_name}")
                    
                    # 골드순 정렬
                    weekly_tasks.sort(key=lambda x: x['gold_reward'], reverse=True)
                    
                    if not weekly_tasks:
                        st.caption("주간 숙제 없음")
                    else:
                        for task in weekly_tasks:
                            is_done = (task['current_count'] >= task['total_count'])
                            label = f"{task['task_name']} - {task['gold_reward']:,} G"
                            if task['total_count'] > 1:
                                label += f" ({task['current_count']}/{task['total_count']})"
                            
                            checked = st.checkbox(label, value=is_done, key=f"chk_w_{task['id']}")
                            if checked != is_done:
                                _update_task_status(task['id'], task['total_count'], checked)

                elif target_tab == "DAILY":
                    st.checkbox("카.가.길", key=f"kagagil_{char_name}")
                    daily_tasks = [t for t in my_tasks if t['category'] == '일일']
                    for task in daily_tasks:
                        is_done = (task['current_count'] >= task['total_count'])
                        checked = st.checkbox(task['task_name'], value=is_done, key=f"chk_d_{task['id']}")
                        if checked != is_done:
                            _update_task_status(task['id'], task['total_count'], checked)

                st.markdown("<hr class='half-margin'>", unsafe_allow_html=True)

                # C. 경제 및 메모
                c1, c2 = st.columns([1, 1])
                with c1:
                    spent = st.number_input("사용 골드", min_value=0, step=100, value=char['week_gold_spent'], key=f"spent_{char_name}_{target_tab}", placeholder="0")
                    if spent != char['week_gold_spent']:
                        update_spent_gold(char_name, spent)
                        st.rerun()
                with c2:
                    st.markdown(f"""
                        <div class="economy-container">
                            <div class="economy-label">예상 수익</div>
                            <div class="economy-value">+{total_income:,} G</div>
                        </div>
                    """, unsafe_allow_html=True)

                memo = st.text_area("메모", value=char['memo'] if char['memo'] else "", height=68, key=f"memo_{char_name}_{target_tab}", label_visibility="collapsed", placeholder="메모...")
                if memo != (char['memo'] if char['memo'] else ""):
                    update_memo(char_name, memo)
                    st.rerun()

def _update_task_status(task_id, total_count, is_checked):
    new_val = total_count if is_checked else 0
    with PostgresDB() as cur:
        cur.execute("UPDATE todos SET current_count = %s WHERE id = %s", (new_val, task_id))
    st.rerun()