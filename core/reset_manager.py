from datetime import datetime, timedelta, timezone
from core.database import PostgresDB

KST = timezone(timedelta(hours=9))

def get_last_reset_times():
    """기존 리셋 기준 시간 계산 (일일/주간)"""
    now = datetime.now(KST)
    today_6am = now.replace(hour=6, minute=0, second=0, microsecond=0)
    
    # 1. 일일 리셋 (매일 06:00)
    if now < today_6am:
        last_daily_reset = today_6am - timedelta(days=1)
    else:
        last_daily_reset = today_6am
        
    # 2. 주간 리셋 (수요일 06:00)
    days_since_wed = (now.weekday() - 2) % 7
    if days_since_wed == 0 and now < today_6am:
        days_since_wed = 7
    last_weekly_reset_day = now - timedelta(days=days_since_wed)
    last_weekly_reset = last_weekly_reset_day.replace(hour=6, minute=0, second=0, microsecond=0)
    
    return last_daily_reset, last_weekly_reset

def check_and_reset_tasks():
    last_daily, last_weekly = get_last_reset_times()
    reset_log = []
    
    try:
        with PostgresDB() as cur:
            # -------------------------------------------------
            # 1. 캐릭터 숙제 리셋 (기존 로직)
            # -------------------------------------------------
            daily_sql = "UPDATE todos SET current_count = 0 WHERE category = '일일' AND current_count > 0 AND updated_at < %s;"
            cur.execute(daily_sql, (last_daily,))
            if cur.rowcount > 0: reset_log.append(f"🌞 일일 숙제 {cur.rowcount}건 초기화")
            
            weekly_sql = "UPDATE todos SET current_count = 0 WHERE category = '주간' AND current_count > 0 AND updated_at < %s;"
            cur.execute(weekly_sql, (last_weekly,))
            if cur.rowcount > 0: reset_log.append(f"📅 주간 숙제 {cur.rowcount}건 초기화")

            # -------------------------------------------------
            # 2. [NEW] 원정대 숙제 맞춤형 리셋
            # -------------------------------------------------
            cur.execute("SELECT id, task_name, reset_type, reset_value, updated_at FROM expedition_tasks WHERE is_checked = TRUE")
            tasks = cur.fetchall()
            
            exp_reset_count = 0
            for t in tasks:
                should_reset = False
                updated_at = t['updated_at'].astimezone(KST) # DB 시간 -> KST 변환
                
                if t['reset_type'] == 'DAILY':
                    # 마지막 수행 시간이 '오늘 오전 6시' 이전이면 리셋
                    if updated_at < last_daily:
                        should_reset = True
                        
                elif t['reset_type'] == 'WEEKLY':
                    # 마지막 수행 시간이 '이번주 수요일 6시' 이전이면 리셋
                    if updated_at < last_weekly:
                        should_reset = True
                        
                elif t['reset_type'] == 'INTERVAL':
                    # N일 간격 (예: 2일)
                    # 수행한지 N일이 지났는지 체크 (단순히 시간 차이로 계산)
                    # 로아 스타일: 수행일로부터 N일 뒤 오전 6시에 리셋? 
                    # 사용자 요청: "2일에 한번" -> 수행 후 48시간 or D+2일
                    # 여기선 심플하게: (현재시간 - 수행시간).days >= N 이면 리셋
                    diff = datetime.now(KST) - updated_at
                    if diff.days >= t['reset_value']:
                        should_reset = True
                
                if should_reset:
                    cur.execute("UPDATE expedition_tasks SET is_checked = FALSE WHERE id = %s", (t['id'],))
                    exp_reset_count += 1
            
            if exp_reset_count > 0:
                reset_log.append(f"🏰 원정대 숙제 {exp_reset_count}건 초기화")

    except Exception as e:
        print(f"리셋 검사 중 오류: {e}")
        
    return reset_log