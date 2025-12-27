import streamlit as st
import sys

from core.database import init_db, PostgresDB

st.set_page_config(page_title="LOA AGENT v2", page_icon="🛡️")

st.title("🛡️ LOA AGENT v2: Architecture Rebuild")

if st.sidebar.button(" DB 초기화 (테이블 생성)"):
    with st.spinner("테이블 생성중 ..."):
        init_db()
        st.success ("초기화 완료")

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



st.write(f"Python Version: {sys.version}")
st.write("Development Environment: Setup Complete!")