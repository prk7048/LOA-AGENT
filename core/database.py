import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

class PostgresDB:
    """
    PostgreSQL 데이터베이스 연결을 관리하는 클래스 (Context Manager 지원)
    사용법:
        with PostgresDB() as db:
            db.execute("SELECT * FROM ...")
    """
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """with 문에 진입할 때 실행 (연결)"""
        try:
            self.conn = psycopg2.connect(
                host = os.getenv("POSTGRES_HOST"),
                database=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                port=os.getenv("POSTGRES_PORT")
            )

            # 결과를 딕셔너리 형태 {'name' : '캐릭터명', 'lv' : 1680} 형식으로 받아준다.
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            return self.cursor
        except Exception as e:
            print(f"DB 연결 실패: {e}")
            raise e
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """with 문을 빠져나갈 때  실행 (자원 해제)"""
        if self.cursor:
            self.cursor.close()

        if self.conn:
            if exc_type:
                self.conn.rollback() # 에러시 롤백
            else:
                self.conn.commit()   # 정상종료시 커밋
            self.conn.close()

def init_db():
    """ 필요한 테이블 생성 """
    create_character_table_sql="""
    CREATE TABLE IF NOT EXISTS characters (
        character_name VARCHAR(50) PRIMARY KEY,
        server_name VARCHAR(20),
        character_class VARCHAR(20),
        item_avg_level FLOAT,
        combat_power FLOAT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """

    print (" DB 데이터 초기화 중...")
    try:
        with PostgresDB() as cur:
            cur.execute(create_character_table_sql)
            print("'characters' 테이블 준비 완료")
    except Exception as e:
        print(f"테이블 생성 중 오류 발생: {e}")

def upsert_character(char_data):
    """
    캐릭터 정보 DB에 저장하거나 갱신
    char_data: {'CharacterName': '은제', 'ServerName': '루페온', ...} 형태의 딕셔너리
    """

    sql = """
    INSERT INTO characters (character_name, server_name, character_class, item_avg_level, combat_power)
    VALUES (%(CharacterName)s, %(ServerName)s, %(CharacterClassName)s, %(ItemAvgLevel)s, %(CombatPower)s)
    ON CONFLICT (character_name)
    DO UPDATE SET
        item_avg_level = EXCLUDED.item_avg_level,
        combat_power = EXCLUDED.combat_power,
        updated_at = CURRENT_TIMESTAMP;
    """

    try:
        with PostgresDB() as cur:
            # 딕셔너리를 통째로 넘기면, %(Key)s 부분에 알아서 들어감
            cur.execute(sql, char_data)
            print(f"저장완료 {char_data['CharacterName']}")
    except Exception as e:
        print(f"저장 실패 {e}")
            