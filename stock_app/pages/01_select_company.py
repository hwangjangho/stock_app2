import streamlit as st
from src.ui.common import init_state
from src.data_sources.dart import get_dart_key, load_corpcode_table, search_corp

init_state()
st.title("회사 선택")

KR_TOP5 = [
    {"name": "삼성전자", "hint": "005930"},
    {"name": "SK하이닉스", "hint": "000660"},
    {"name": "현대차", "hint": "005380"},
    {"name": "LG화학", "hint": "051910"},
    {"name": "NAVER", "hint": "035420"},
]
US_TOP5 = [
    {"name": "Apple", "ticker": "AAPL"},
    {"name": "Microsoft", "ticker": "MSFT"},
    {"name": "NVIDIA", "ticker": "NVDA"},
    {"name": "Amazon", "ticker": "AMZN"},
    {"name": "Alphabet", "ticker": "GOOGL"},
]

@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def cached_corp_table(api_key: str):
    return load_corpcode_table(api_key)

api_key = get_dart_key()

country = st.selectbox(
    "시장",
    options=["KR", "US"],
    index=0 if st.session_state["country"] != "US" else 1
)

st.divider()

if country == "KR":
    st.subheader("한국(KR): 회사명 검색 → 자동으로 corp_code + ticker(6자리.KS) 설정")

    if not api_key:
        st.error("환경변수 DART_API_KEY가 필요합니다. (KR 재무/검색 기능)")
        st.stop()

    with st.spinner("DART corpCode 로딩(1일 캐시)..."):
        corp_rows = cached_corp_table(api_key)

    keyword = st.text_input("회사명 검색", value=st.session_state["company_name"], placeholder="예: 삼성전자")

    matches = search_corp(corp_rows, keyword, limit=30)

    if matches:
        labels = [
            f"{m['corp_name']} | stock_code={m['stock_code'] or '-'} | corp_code={m['corp_code']}"
            for m in matches
        ]
        idx = st.selectbox("검색 결과", options=list(range(len(labels))), format_func=lambda i: labels[i])
        chosen = matches[idx]

        if st.button("이 회사 선택", type="primary"):
            st.session_state["country"] = "KR"
            st.session_state["company_name"] = chosen["corp_name"]
            st.session_state["corp_code"] = chosen["corp_code"]

            sc = (chosen.get("stock_code") or "").strip()
            st.session_state["ticker"] = f"{sc}.KS" if sc else ""
            st.success("저장 완료 (corp_code/ticker 포함).")

    else:
        st.info("검색 결과가 없으면, 아래 우량주 버튼으로 선택해보세요.")

    st.divider()
    st.subheader("국내 우량주 5개 (버튼 선택)")
    cols = st.columns(5)
    for i, item in enumerate(KR_TOP5):
        with cols[i]:
            if st.button(item["name"], use_container_width=True):
                # 버튼은 키워드 입력만 도와주고, 최종 선택은 검색결과에서 corp_code 확정하도록 유도
                st.session_state["company_name"] = item["name"]
                st.session_state["country"] = "KR"
                st.info("위 검색창에 자동 입력된 회사명으로 검색 결과에서 정확한 항목을 선택해 주세요.")
                st.rerun()

else:
    st.subheader("미국(US): 티커로 선택(예: AAPL)")

    ticker = st.text_input("미국 티커", value=st.session_state["ticker"] if st.session_state["country"]=="US" else "", placeholder="예: AAPL")
    company = st.text_input("회사명(표시용)", value=st.session_state["company_name"] if st.session_state["country"]=="US" else "", placeholder="예: Apple")

    if st.button("US 회사 선택 적용", type="primary"):
        st.session_state["country"] = "US"
        st.session_state["ticker"] = ticker.strip().upper()
        st.session_state["company_name"] = company.strip() or st.session_state["ticker"]
        st.session_state["corp_code"] = ""
        st.success("저장 완료.")

    st.divider()
    st.subheader("해외(US) 우량주 Top 5 (클릭 선택)")
    cols = st.columns(5)
    for i, item in enumerate(US_TOP5):
        with cols[i]:
            if st.button(item["name"], use_container_width=True):
                st.session_state["country"] = "US"
                st.session_state["company_name"] = item["name"]
                st.session_state["ticker"] = item["ticker"]
                st.session_state["corp_code"] = ""
                st.success(f"선택: {item['name']}")
                st.rerun()

st.divider()
st.write("현재 선택:")
st.json({k: st.session_state[k] for k in ["company_name", "ticker", "country", "corp_code"]})