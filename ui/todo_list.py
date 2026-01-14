import streamlit as st
from core.database import PostgresDB, update_memo, update_spent_gold

def render_todo_list():
    """숙제 리스트 렌더링 메인 함수"""
    
    # 1. 원정대 숙제 (UI만 유지)
    with st.container(border=True):
        st.markdown("### 🏰 원정대 통합 숙제")
        exp_tasks = ["길드 출석", "영지 파견", "도가토/도연", "주간 에포나", "카게/필보"]
        cols = st.columns(len(exp_tasks)) # 가로로 배치하거나 세로로 배치 (취향껏)
        for i, task in enumerate(exp_tasks):
            st.checkbox(task, key=f"exp_{i}")

    st.write("") 

    # 2. 탭 분리
    sub_tab_weekly, sub_tab_daily = st.tabs(["📅 주간 숙제", "⚡ 일일 숙제"])

    # 3. 데이터 가져오기
    try:
        with PostgresDB() as cur:
            # 캐릭터 정보 (메모, 골드 포함)
            cur.execute("SELECT * FROM characters ORDER BY item_avg_level DESC")
            characters = cur.fetchall()

            # 숙제 정보 (골드 보상 포함)
            cur.execute("SELECT * FROM todos ORDER BY id ASC")
            all_todos = cur.fetchall()
            
    except Exception as e:
        st.error(f"데이터 로딩 실패: {e}")
        return

    # 4. 렌더링
    with sub_tab_weekly:
        _render_character_cards(characters, all_todos, "WEEKLY")
    with sub_tab_daily:
        _render_character_cards(characters, all_todos, "DAILY")


def _render_character_cards(characters, all_todos, target_tab):
    """
    캐릭터 카드를 그리는 로직 (최종 수정 버전)
    - 수익 계산 로직을 탭 분기 밖으로 이동 (탭 변경 시에도 수익 유지)
    """
    cols = st.columns(4)
    
    for idx, char in enumerate(characters):
        char_name = char['character_name']
        
        with cols[idx % 4]:
            with st.container(border=True):
                
                # ---------------------------------------------------------
                # A. 헤더 (Header)
                # ---------------------------------------------------------
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

                # ---------------------------------------------------------
                # [핵심 수정] 수익 계산을 탭 렌더링보다 먼저 수행!
                # ---------------------------------------------------------
                my_tasks = [t for t in all_todos if t['character_name'] == char_name]
                
                # 1. 주간 숙제만 발라내기
                weekly_tasks = [t for t in my_tasks if t['category'] == '주간']
                
                # 2. 예상 수익 미리 계산 (탭 상관없이 항상 계산됨)
                # (옵션) 체크된 것만 계산하려면: if t['current_count'] >= t['total_count'] 조건 추가
                # 여기서는 '전체 잠재 수익'을 보여줍니다.
                total_income = sum(t['gold_reward'] for t in weekly_tasks)


                # ---------------------------------------------------------
                # B. 숙제 리스트 (탭에 따라 다르게 표시)
                # ---------------------------------------------------------
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
                    st.checkbox("카.가.길 (통합)", key=f"kagagil_{char_name}")
                    
                    daily_tasks = [t for t in my_tasks if t['category'] == '일일']
                    if daily_tasks:
                        for task in daily_tasks:
                            is_done = (task['current_count'] >= task['total_count'])
                            label = f"{task['task_name']}"
                            
                            checked = st.checkbox(label, value=is_done, key=f"chk_d_{task['id']}")
                            if checked != is_done:
                                _update_task_status(task['id'], task['total_count'], checked)

                st.markdown("<hr class='half-margin'>", unsafe_allow_html=True)

                # ---------------------------------------------------------
                # C. 경제 및 메모
                # ---------------------------------------------------------
                c1, c2 = st.columns([1, 1])
                
                with c1:
                    # 사용 골드 (DB 연동)
                    spent = st.number_input(
                        "사용 골드", min_value=0, step=100, 
                        value=char['week_gold_spent'], 
                        key=f"spent_{char_name}_{target_tab}", 
                        placeholder="0"
                    )
                    if spent != char['week_gold_spent']:
                        update_spent_gold(char_name, spent)
                        st.rerun()
                    
                with c2:
                    # 예상 수익 표시 (아까 계산해둔 total_income 사용)
                    st.markdown(f"""
                        <div class="economy-container">
                            <div class="economy-label">예상 수익</div>
                            <div class="economy-value">+{total_income:,} G</div>
                        </div>
                    """, unsafe_allow_html=True)

                # 메모장
                memo = st.text_area(
                    "메모", 
                    value=char['memo'] if char['memo'] else "", 
                    height=68, 
                    key=f"memo_{char_name}_{target_tab}", 
                    label_visibility="collapsed",
                    placeholder="메모..."
                )
                if memo != (char['memo'] if char['memo'] else ""):
                    update_memo(char_name, memo)
                    st.rerun()

def _update_task_status(task_id, total_count, is_checked):
    new_val = total_count if is_checked else 0
    with PostgresDB() as cur:
        cur.execute("UPDATE todos SET current_count = %s WHERE id = %s", (new_val, task_id))
    st.rerun()