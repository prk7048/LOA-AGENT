# core/reset_manager.py
from datetime import datetime, timedelta, timezone
from core.database import PostgresDB

# 한국 시간대 (KST) 정의
KST = timezone(timedelta(hours=9))

def get_last_reset_times():
    """
    현재 시간을 기준으로 '가장 최근의 리셋 시점'을 계산합니다.
    - 일일 리셋: 오늘 오전 06:00 (아직 안 지났으면 어제 06:00)
    - 주간 리셋: 이번 주 수요일 06:00 (아직 안 지났으면 저번 주 수요일 06:00)
    """
    now = datetime.now(KST)
    
    # 1. 일일 리셋 기준점 (매일 오전 6시)
    today_6am = now.replace(hour=6, minute=0, second=0, microsecond=0)+ timedelta(days=1)
    if now < today_6am:
        last_daily_reset = today_6am - timedelta(days=1)
    else:
        last_daily_reset = today_6am
        
    # 2. 주간 리셋 기준점 (매주 수요일 오전 6시)
    # weekday(): 월=0, 화=1, 수=2 ... 일=6
    days_since_wed = (now.weekday() - 2) % 7
    
    # 만약 오늘이 수요일인데 아직 6시 전이라면? -> 저번 주 수요일이 기준
    if days_since_wed == 0 and now < today_6am:
        days_since_wed = 7
        
    last_weekly_reset_day = now - timedelta(days=days_since_wed)
    last_weekly_reset = last_weekly_reset_day.replace(hour=6, minute=0, second=0, microsecond=0)
    
    return last_daily_reset, last_weekly_reset

def check_and_reset_tasks():
    """
    DB를 조회해서 '마지막 수정 시간(updated_at)'이 
    '리셋 기준 시간'보다 옛날인 숙제들을 0으로 초기화합니다.
    """
    last_daily, last_weekly = get_last_reset_times()
    reset_log = []
    
    try:
        with PostgresDB() as cur:
            # A. 일일 숙제 리셋
            # 조건: 카테고리가 '일일'이고 + 이미 수행했고(count>0) + 마지막 수행 시간이 리셋 시간보다 이전일 때
            daily_sql = """
            UPDATE todos 
            SET current_count = 0 
            WHERE category = '일일' 
              AND current_count > 0
              AND updated_at < %s;
            """
            cur.execute(daily_sql, (last_daily,))
            if cur.rowcount > 0:
                reset_log.append(f"🌞 일일 숙제 {cur.rowcount}건 초기화")
            
            # B. 주간 숙제 리셋
            weekly_sql = """
            UPDATE todos 
            SET current_count = 0 
            WHERE category = '주간' 
              AND current_count > 0
              AND updated_at < %s;
            """
            cur.execute(weekly_sql, (last_weekly,))
            if cur.rowcount > 0:
                reset_log.append(f"📅 주간 숙제 {cur.rowcount}건 초기화")
                
    except Exception as e:
        print(f"리셋 검사 중 오류: {e}")
        
    return reset_log