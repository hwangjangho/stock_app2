import streamlit as st
import pandas as pd
import altair as alt

from src.ui.common import init_state
from src.data_sources.prices import get_price_history
from src.scoring.scenario import scenario_forecast

init_state()
st.title("1년 시나리오 기반 주가 경향 예측")

company = st.session_state.get("company_name") or ""
ticker = st.session_state.get("ticker") or ""
country = st.session_state.get("country") or ""

if not (company and ticker and country):
    st.warning("먼저 1) 회사 선택에서 회사/티커를 선택하세요.")
    st.stop()

st.write({"company": company, "ticker": ticker, "country": country})

# 자동값(없으면 기본)
auto_fund = st.session_state.get("fund_score")
auto_pos = st.session_state.get("pos_score")
auto_neg = st.session_state.get("neg_score")

fallback_fund = 55.0
fallback_pos = 0.50
fallback_neg = 0.25

use_manual = st.checkbox("수동으로 입력(오버라이드)", value=False)

if use_manual:
    fund_score = st.slider("재무 점수(0~100)", 0, 100, int(auto_fund if auto_fund is not None else fallback_fund))
    pos_score = st.slider("뉴스 긍정(0~1)", 0.0, 1.0, float(auto_pos if auto_pos is not None else fallback_pos))
    neg_score = st.slider("뉴스 부정(0~1)", 0.0, 1.0, float(auto_neg if auto_neg is not None else fallback_neg))
else:
    fund_score = float(auto_fund if auto_fund is not None else fallback_fund)
    pos_score = float(auto_pos if auto_pos is not None else fallback_pos)
    neg_score = float(auto_neg if auto_neg is not None else fallback_neg)

    st.info("자동 입력값")
    st.json({
        "fund_score(0~100)": fund_score,
        "pos_score(0~1)": pos_score,
        "neg_score(0~1)": neg_score,
        "note": "재무/뉴스 페이지를 먼저 수행하면 자동값이 실제 계산 결과로 채워집니다.",
    })

with st.spinner("가격 데이터 로딩..."):
    df = get_price_history(country, ticker, years=2)

close = df["close"].dropna().values
trend, scenarios = scenario_forecast(close, fund_score, pos_score, neg_score, days=252)

st.metric("예측 경향(가장 가능성 높은 시나리오 기준)", trend)

scenarios = sorted(scenarios, key=lambda x: x["prob"], reverse=True)

chart_df = []
for s in scenarios:
    for i in range(len(s["t"])):
        chart_df.append({
            "day": int(s["t"][i]),
            "scenario": s["scenario"],
            "prob": s["prob"],
            "median": float(s["median"][i]),
            "upper": float(s["upper"][i]),
            "lower": float(s["lower"][i]),
        })
cdf = pd.DataFrame(chart_df)

st.subheader("시나리오 5개(확률 높은 순)")
st.dataframe(pd.DataFrame([{
    "scenario": s["scenario"],
    "prob": round(s["prob"], 3),
    "mu(annual)": round(s["mu"], 3),
    "sigma(annual)": round(s["sigma"], 3),
} for s in scenarios]), use_container_width=True)

base = alt.Chart(cdf).encode(
    x=alt.X("day:Q", title="거래일(0~252)"),
    color=alt.Color("scenario:N", legend=alt.Legend(title="Scenario")),
)

band = base.mark_area(opacity=0.15).encode(
    y=alt.Y("lower:Q", title="Price (forecast range)"),
    y2="upper:Q",
    tooltip=["scenario", "prob", "day", "lower", "upper"]
)

line = base.mark_line(size=2).encode(
    y="median:Q",
    tooltip=["scenario", "prob", "day", "median"]
)

st.altair_chart(band + line, use_container_width=True)