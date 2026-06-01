import streamlit as st

def init_state():
    st.session_state.setdefault("company_name", "")
    st.session_state.setdefault("country", "")        # "KR" or "US"
    st.session_state.setdefault("ticker", "")         # "005930.KS" or "AAPL"
    st.session_state.setdefault("corp_code", "")      # DART corp_code (KR only)

    st.session_state.setdefault("news_source", "WSJ")
    st.session_state.setdefault("news_source_url", "")

    # outputs to carry between pages
    st.session_state.setdefault("fund_score", None)   # 0..100
    st.session_state.setdefault("fund_details", None) # dict
    st.session_state.setdefault("pos_score", None)    # 0..1
    st.session_state.setdefault("neg_score", None)    # 0..1
    st.session_state.setdefault("news_items", None)   # list