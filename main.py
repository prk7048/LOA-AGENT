import streamlit as st
import sys

from core.database import init_db, PostgresDB, upsert_character

st.set_page_config(page_title="LOA AGENT v2", page_icon="🛡️")

st.title("🛡️ LOA AGENT v2: Architecture Rebuild")

with st.sidebar:
    if st.button(" DB 완전 초기화 (테이블 생성)"):
        with st.spinner("테이블 생성중 ..."):
            try :
                with PostgresDB() as cur :
                    cur.execute("DROP TABLE IF EXISTS characters;")
                init_db()
                st.success ("테이블 최신업데이트 완료")
            except Exception as e:
                st.error(f"초기화 실패 {e}")






st.subheader("저장된 캐릭터 목록(DB 조회)")

try:
    with PostgresDB() as cur:
        cur.execute("SELECT * FROM characters")
        rows = cur.fetchall()

        if rows:
            st.write(rows)
        else:
            st.info("noData yes Table")

except Exception as e:
    st.error(f"DB 연결 오류 {e}")

if st.button(" 더미 데이터 넣기 (TEST)"):
    dummy_data = [
        {"CharacterName": "본캐임", "ServerName": "루페온", "CharacterClassName": "워로드", "ItemAvgLevel": 1680.0, "CombatPower" : 5000.0},
        {"CharacterName": "배럭1", "ServerName": "카단", "CharacterClassName": "바드", "ItemAvgLevel": 1640.5, "CombatPower" : 4000.0},
        {"CharacterName": "배럭2", "ServerName": "아만", "CharacterClassName": "소서리스", "ItemAvgLevel": 1620.83, "CombatPower" : 3500.2},
    ]

    for char in dummy_data:
        upsert_character(char)

    st.success(f"{len(dummy_data)}명의 캐릭터가 저장됨")
    st.rerun()

st.subheader (" 현 DB 목록 ")
with PostgresDB() as cur:
    cur.execute("SELECT * FROM characters")
    rows = cur.fetchall()
    st.dataframe(rows)

st.write(f"Python Version: {sys.version}")
st.write("Development Environment: Setup Complete!")