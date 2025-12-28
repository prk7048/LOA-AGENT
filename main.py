import streamlit as st
import sys
from dotenv import load_dotenv

load_dotenv()

from core.database import init_db, PostgresDB, upsert_character
from core.loa_api import LostArkAPI

st.set_page_config(page_title="LOA AGENT v2", page_icon="🛡️")

st.title("🛡️ LOA AGENT v2: Architecture Rebuild")

st.subheader("캐릭터 검색 & DB 저장")

col1, col2 = st.columns([3,1])

with col1:
    target_name = "은제1"

with col2:
    st.write("")
    st.write("")
    search_btn = st.button("검색 및 저장", use_container_width=True)

if search_btn and target_name:
    api = LostArkAPI()

    with st.spinner(f"'{target_name}' 정보를 로스트아크 서버에서 가져오는 중"):
        # API 호출
        profile_data = api.get_character_profile(target_name)

        if profile_data:
            # 성공시 DB 저장
            upsert_character(profile_data)
            st.success(f"저장 완료 {profile_data['CharacterName']} ({profile_data['ItemAvgLevel']})")
            st.rerun()

        else:
            st.error("캐릭터를 찾을수 없거나 API 오류 발생")

# --- [UI] 저장된 목록 조회 (기존 코드 유지) ---
st.divider()
st.subheader("📊 내 원정대 리스트")

try:
    with PostgresDB() as cur:
        cur.execute ("SELECT * FROM characters ORDER BY updated_at DESC")
        rows = cur.fetchall()
        st.dataframe(rows, use_container_width=True)

except Exception as e:
    st.error(f"DB 조회 오류 : {e}")


# with st.sidebar:
#     if st.button(" DB 완전 초기화 (테이블 생성)"):
#         with st.spinner("테이블 생성중 ..."):
#             try :
#                 with PostgresDB() as cur :
#                     cur.execute("DROP TABLE IF EXISTS characters;")
#                 init_db()
#                 st.success ("테이블 최신업데이트 완료")
#             except Exception as e:
#                 st.error(f"초기화 실패 {e}")



# st.subheader("저장된 캐릭터 목록(DB 조회)")

# try:
#     with PostgresDB() as cur:
#         cur.execute("SELECT * FROM characters")
#         rows = cur.fetchall()

#         if rows:
#             st.write(rows)
#         else:
#             st.info("noData yes Table")

# except Exception as e:
#     st.error(f"DB 연결 오류 {e}")

# if st.button(" 더미 데이터 넣기 (TEST)"):
#     dummy_data = [
#         {"CharacterName": "본캐임", "ServerName": "루페온", "CharacterClassName": "워로드", "ItemAvgLevel": 1680.0, "CombatPower" : 5000.0},
#         {"CharacterName": "배럭1", "ServerName": "카단", "CharacterClassName": "바드", "ItemAvgLevel": 1640.5, "CombatPower" : 4000.0},
#         {"CharacterName": "배럭2", "ServerName": "아만", "CharacterClassName": "소서리스", "ItemAvgLevel": 1620.83, "CombatPower" : 3500.2},
#     ]

#     for char in dummy_data:
#         upsert_character(char)

#     st.success(f"{len(dummy_data)}명의 캐릭터가 저장됨")
#     st.rerun()

# st.subheader (" 현 DB 목록 ")
# with PostgresDB() as cur:
#     cur.execute("SELECT * FROM characters")
#     rows = cur.fetchall()
#     st.dataframe(rows)
