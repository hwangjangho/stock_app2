import streamlit as st

openai_key = st.secrets["OPENAI_API_KEY"]
dart_key = st.secrets["DART_API_KEY"]

st.set_page_config(page_title="주가 예측 프로그램", layout="wide")

pages = [
    st.Page("pages/01_select_company.py", title="1) 회사 선택", icon="🔎"),
    st.Page("pages/02_fundamentals_score.py", title="2) 재무 점수", icon="📊"),
    st.Page("pages/03_news_sentiment.py", title="3) 뉴스 감성", icon="📰"),
    st.Page("pages/04_forecast.py", title="4) 1년 시나리오 예측", icon="📈"),
]

nav = st.navigation(pages)
nav.run()
