import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from core.game_data import calculate_best_raids

load_dotenv()

class PostgresDB:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST"),
                database=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                port=os.getenv("POSTGRES_PORT")
            )
            self.conn.autocommit = True
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            return self.cursor
        except Exception as e:
            raise e
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor: self.cursor.close()
        if self.conn: self.conn.close()

def init_db():
    """DB 테이블 구조 생성 (없을 때만)"""
    create_character_table_sql = """
    CREATE TABLE IF NOT EXISTS characters (
        character_name VARCHAR(50) PRIMARY KEY,
        server_name VARCHAR(20),
        character_class VARCHAR(20),
        item_avg_level FLOAT,
        combat_power INT,
        week_gold_spent INT DEFAULT 0,
        memo TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    create_todos_table_sql = """
    CREATE TABLE IF NOT EXISTS todos (
        id SERIAL PRIMARY KEY,
        character_name VARCHAR(50) NOT NULL,
        game_name VARCHAR(20) DEFAULT 'LostArk',
        task_name VARCHAR(100) NOT NULL,
        category VARCHAR(20) DEFAULT '일일',
        current_count INT DEFAULT 0,
        total_count INT DEFAULT 1,
        reset_cycle VARCHAR(20) DEFAULT 'DAILY',
        gold_reward INT DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_character FOREIGN KEY(character_name) REFERENCES characters(character_name) ON DELETE CASCADE,
        CONSTRAINT unique_task_per_char UNIQUE (character_name, task_name)
    );
    """
    create_exp_tasks_sql = """
    CREATE TABLE IF NOT EXISTS expedition_tasks (
        id SERIAL PRIMARY KEY,
        task_name VARCHAR(100) NOT NULL UNIQUE,
        is_checked BOOLEAN DEFAULT FALSE,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    create_settings_sql = """
    CREATE TABLE IF NOT EXISTS app_settings (
        key VARCHAR(50) PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with PostgresDB() as cur:
            cur.execute(create_character_table_sql)
            cur.execute(create_todos_table_sql)
            cur.execute(create_exp_tasks_sql)
            cur.execute(create_settings_sql)
    except Exception as e:
        print(f"❌ 테이블 생성 오류: {e}")

# 👇 [NEW] 진짜로 데이터를 다 날리는 함수 추가 👇
def reset_db():
    """기존 데이터를 모두 삭제하고 테이블을 재생성합니다."""
    try:
        with PostgresDB() as cur:
            # 테이블을 강제로 삭제 (CASCADE로 연관 데이터도 삭제)
            cur.execute("DROP TABLE IF EXISTS todos CASCADE;")
            cur.execute("DROP TABLE IF EXISTS characters CASCADE;")
            cur.execute("DROP TABLE IF EXISTS expedition_tasks CASCADE;")
            # 설정(app_settings)은 남길지 선택할 수 있지만, '완전 초기화'니까 다 지웁니다.
            cur.execute("DROP TABLE IF EXISTS app_settings CASCADE;")
            print("🗑️ 기존 데이터 삭제 완료")
            
        # 다시 생성
        init_db()
        print("✨ DB 재설정 완료")
    except Exception as e:
        print(f"❌ DB 리셋 실패: {e}")

def upsert_character(char_data):
    name = char_data["CharacterName"]
    try:
        avg_level = float(str(char_data["ItemAvgLevel"]).replace(",", ""))
    except:
        avg_level = 0.0
    new_cp = int(char_data.get("CombatPower", 0) or 0)
    
    try:
        with PostgresDB() as cur:
            cur.execute("SELECT combat_power FROM characters WHERE character_name = %s", (name,))
            row = cur.fetchone()
            final_cp = new_cp
            if row and row['combat_power'] > new_cp:
                final_cp = row['combat_power']

            sql = """
            INSERT INTO characters (character_name, server_name, character_class, item_avg_level, combat_power)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (character_name)
            DO UPDATE SET
                item_avg_level = EXCLUDED.item_avg_level,
                combat_power = %s,
                updated_at = CURRENT_TIMESTAMP;
            """
            cur.execute(sql, (
                char_data["CharacterName"],
                char_data["ServerName"],
                char_data["CharacterClassName"],
                avg_level,
                final_cp,
                final_cp
            ))
        refresh_weekly_raids(name, avg_level, final_cp)
        add_daily_tasks(name)
    except Exception as e:
        print(f"❌ {name} 저장 실패: {e}")

def refresh_weekly_raids(character_name, item_lv, combat_power):
    best_raids = calculate_best_raids(item_lv, combat_power)
    if not best_raids: return
    try:
        with PostgresDB() as cur:
            new_task_names = [f"{r['name']} ({r['difficulty']})" for r in best_raids]
            if new_task_names:
                placeholders = ",".join(["%s"] * len(new_task_names))
                delete_sql = f"DELETE FROM todos WHERE character_name = %s AND category = '주간' AND task_name NOT IN ({placeholders});"
                cur.execute(delete_sql, (character_name, *new_task_names))
            
            upsert_sql = "INSERT INTO todos (character_name, game_name, task_name, category, total_count, reset_cycle, gold_reward) VALUES (%s, 'LostArk', %s, '주간', 1, 'WEEKLY', %s) ON CONFLICT (character_name, task_name) DO UPDATE SET gold_reward = EXCLUDED.gold_reward;"
            for r in best_raids:
                full_name = f"{r['name']} ({r['difficulty']})"
                cur.execute(upsert_sql, (character_name, full_name, r['gold']))
    except Exception as e:
        print(f"❌ 주간 갱신 실패: {e}")

def add_daily_tasks(character_name):
    defaults = [("카오스 던전", 1), ("가디언 토벌", 1)]
    sql = "INSERT INTO todos (character_name, task_name, category, total_count, reset_cycle, gold_reward) VALUES (%s, %s, '일일', %s, 'DAILY', 0) ON CONFLICT (character_name, task_name) DO NOTHING;"
    try:
        with PostgresDB() as cur:
            for task, count in defaults:
                cur.execute(sql, (character_name, task, count))
    except: pass

def update_memo(char_name, memo_text):
    with PostgresDB() as cur:
        cur.execute("UPDATE characters SET memo = %s WHERE character_name = %s", (memo_text, char_name))

def update_spent_gold(char_name, amount):
    with PostgresDB() as cur:
        cur.execute("UPDATE characters SET week_gold_spent = %s WHERE character_name = %s", (amount, char_name))

def set_app_setting(key, value):
    with PostgresDB() as cur:
        cur.execute("INSERT INTO app_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", (key, str(value)))

def get_app_setting(key):
    with PostgresDB() as cur:
        cur.execute("SELECT value FROM app_settings WHERE key = %s", (key,))
        res = cur.fetchone()
        return res['value'] if res else None