import streamlit as st
from datetime import date
from src.ui.common import init_state
from src.data_sources.dart import get_dart_key, get_financials_single_company, extract_basic_metrics
from src.scoring.fundamentals import fundamentals_score_kr

init_state()
st.title("재무 점수 (0~100)")

country = st.session_state.get("country")
if country != "KR":
    st.info("현재 구현: KR은 DART 재무점수 제공. US는 추후(유료/제한 없는 데이터 소스 필요) 확장 권장.")
    st.stop()

api_key = get_dart_key()
if not api_key:
    st.error("환경변수 DART_API_KEY가 필요합니다.")
    st.stop()

corp_code = (st.session_state.get("corp_code") or "").strip()
company = st.session_state.get("company_name") or ""

st.write({"company": company, "corp_code": corp_code, "ticker": st.session_state.get("ticker")})

if len(corp_code) != 8:
    st.warning("1) 회사 선택에서 corp_code가 설정되도록 회사 검색 후 선택해주세요.")
    st.stop()

bsns_year = st.number_input(
    "사업연도",
    min_value=2015,
    max_value=date.today().year,
    value=max(2015, date.today().year - 1),
    step=1,
)
reprt_code = st.selectbox("보고서", ["11011", "11012", "11013", "11014"], index=0)
fs_div = st.selectbox("연결/별도", ["CFS", "OFS"], index=0)

if st.button("재무 조회 & 점수 계산", type="primary"):
    with st.spinner("DART 재무 조회 중..."):
        fin = get_financials_single_company(api_key, corp_code, int(bsns_year), reprt_code, fs_div)

    metrics, err = extract_basic_metrics(fin)
    if err:
        st.error(err)
        st.json(fin)
        st.stop()

    total, parts, extras = fundamentals_score_kr(metrics)

    detail = {
        "inputs": {"bsns_year": int(bsns_year), "reprt_code": reprt_code, "fs_div": fs_div},
        "raw_metrics": metrics,
        "derived": extras,
        "component_scores": parts,
        "note": "MVP 스코어. 업종별 기준치/성장률/현금흐름 등을 추가하면 더 현실적인 점수로 개선 가능.",
    }

    st.session_state["fund_score"] = float(total)
    st.session_state["fund_details"] = detail

    st.metric("재무 점수", f"{total:.1f} / 100")
    st.subheader("근거(원자료/계산)")
    st.json(detail)