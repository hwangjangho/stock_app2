
from __future__ import annotations


import streamlit as st


from src.analysis.sentiment import apply_sentiment_to_df, summarize_sentiment


st.set_page_config(page_title="뉴스 감성 분석", page_icon="📰", layout="wide")


# ---------------------------------
# 예시용 뉴스 로더
# ---------------------------------
# 실제 프로젝트에 뉴스 수집 함수가 있으면
# 아래 함수를 지우고 기존 함수로 바꾸세요.
def load_news(company_name, max_news=20):
    """
    회사명을 기반으로 Google News RSS에서 뉴스 제목을 수집하고,
    제목에 실제로 자주 등장한 키워드와 관련 키워드를 함께 반환합니다.

    반환 형식:
    [
        {
            "title": "...",
            "link": "...",
            "published": "...",
            "keywords": ["키워드1", "키워드2", ...],
            "related_keywords": ["연관어1", "연관어2", ...]
        },
        ...
    ]
    """

    rss_url = f"https://news.google.com/rss/search?q={company_name}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)

    # 뉴스 원본 수집
    news_items = []
    titles = []

    for entry in feed.entries[:max_news]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        published = entry.get("published", "").strip()

        if title:
            news_items.append({
                "title": title,
                "link": link,
                "published": published
            })
            titles.append(title)

    # 뉴스가 없으면 빈 리스트 반환
    if not news_items:
        return []

    # 불용어 설정
    stopwords = {
        company_name,
        "뉴스", "속보", "기자", "단독", "관련", "시장", "기업", "업계",
        "오늘", "이번", "해당", "통해", "대한", "이후", "전망", "기준",
        "발표", "최대", "증가", "감소", "주요", "진행", "분석", "기록",
        "에서", "으로", "했다", "한다", "되는", "있는", "있다", "위해",
        "그리고", "또한", "대한", "종목", "주가", "투자", "실적", "대표",
        "회장", "사업", "계획", "추진", "확대", "검토", "…", "및"
    }

    # 전체 뉴스 제목에서 단어/2단어 조합 빈도 수집
    word_counter = Counter()
    bigram_counter = Counter()

    title_words_list = []

    for title in titles:
        words = re.findall(r"[가-힣A-Za-z0-9]+", title)
        filtered_words = []

        for word in words:
            word = word.strip()
            if len(word) < 2:
                continue
            if word in stopwords:
                continue
            if company_name in word:
                continue
            filtered_words.append(word)

        title_words_list.append(filtered_words)
        word_counter.update(filtered_words)

        for i in range(len(filtered_words) - 1):
            bigram = f"{filtered_words[i]} {filtered_words[i+1]}"
            bigram_counter[bigram] += 1

    # 전체 기준 상위 키워드
    top_keywords = [word for word, _ in word_counter.most_common(10)]
    top_related_keywords = [bigram for bigram, _ in bigram_counter.most_common(10)]

    # 각 뉴스별 키워드도 같이 붙여서 반환
    result = []
    for idx, item in enumerate(news_items):
        local_keywords = []
        for word in title_words_list[idx]:
            if word not in local_keywords:
                local_keywords.append(word)

        result.append({
            "title": item["title"],
            "link": item["link"],
            "published": item["published"],
            "keywords": local_keywords[:5],                # 해당 기사 기준 키워드
            "related_keywords": top_related_keywords[:5],  # 전체 기사 기준 연관 키워드
            "top_keywords": top_keywords[:10]              # 전체 핵심 키워드
        })

    return result


# ---------------------------------
# 실제 뉴스 로더 연결용
# ---------------------------------
import pandas as pd
import re
import feedparser
from collections import Counter


def load_news(ticker: str, limit: int = 30) -> pd.DataFrame:
    """
    ticker(또는 회사명) 기준으로 Google News RSS에서 뉴스를 수집해
    DataFrame으로 반환합니다.

    반환 컬럼:
    - title
    - link
    - published
    - keyword
    - related_keywords
    - source
    """

    rss_url = f"https://news.google.com/rss/search?q={ticker}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)

    rows = []
    titles = []

    for entry in feed.entries[:limit]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        published = entry.get("published", "").strip()

        if title:
            titles.append(title)
            rows.append({
                "title": title,
                "link": link,
                "published": published,
                "source": "Google News"
            })

    if not rows:
        return pd.DataFrame(columns=[
            "title", "link", "published", "keyword", "related_keywords", "source"
        ])

    stopwords = {
        ticker,
        "뉴스", "속보", "기자", "단독", "관련", "시장", "기업", "업계",
        "오늘", "이번", "해당", "통해", "대한", "이후", "전망", "기준",
        "발표", "최대", "증가", "감소", "주요", "진행", "분석", "기록",
        "에서", "으로", "했다", "한다", "되는", "있는", "있다", "위해",
        "그리고", "또한", "종목", "주가", "투자", "실적", "대표",
        "회장", "사업", "계획", "추진", "확대", "검토", "및"
    }

    word_counter = Counter()
    bigram_counter = Counter()
    title_words = []

    for title in titles:
        words = re.findall(r"[가-힣A-Za-z0-9]+", title)
        filtered = []

        for word in words:
            if len(word) < 2:
                continue
            if word in stopwords:
                continue
            if ticker in word:
                continue
            filtered.append(word)

        title_words.append(filtered)
        word_counter.update(filtered)

        for i in range(len(filtered) - 1):
            bigram = f"{filtered[i]} {filtered[i + 1]}"
            bigram_counter[bigram] += 1

    top_keywords = [word for word, _ in word_counter.most_common(10)]
    top_related_keywords = [pair for pair, _ in bigram_counter.most_common(10)]

    for i, row in enumerate(rows):
        local_keywords = []
        for word in title_words[i]:
            if word not in local_keywords:
                local_keywords.append(word)

        row["keyword"] = ", ".join(local_keywords[:5]) if local_keywords else ""
        row["related_keywords"] = ", ".join(top_related_keywords[:5]) if top_related_keywords else ""

    df = pd.DataFrame(rows)
    return df


# ---------------------------------
# UI
# ---------------------------------
st.title("📰 뉴스 감성 분석")
st.caption("뉴스 제목 기반 한국어 금융 감성 분석 결과를 보여줍니다.")

with st.sidebar:
    st.header("조회 조건")
    ticker = st.text_input("종목/키워드", value="")
    limit = st.slider("뉴스 개수", min_value=5, max_value=100, value=20, step=5)
    run = st.button("감성 분석 실행", use_container_width=True)


if run:
    try:
        news_df = load_news(ticker=ticker, limit=limit)

        if news_df is None or news_df.empty:
            st.warning("조회된 뉴스가 없습니다.")
            st.stop()

        if "title" not in news_df.columns:
            st.error("뉴스 데이터에 'title' 컬럼이 없습니다.")
            st.stop()

        analyzed_df = apply_sentiment_to_df(news_df, text_col="title")
        summary = summarize_sentiment(analyzed_df)

        # -------------------------------
        # 요약 지표
        # -------------------------------
        st.subheader("감성 분석 요약")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("평균 점수", summary["avg_score"])
        c2.metric("긍정", summary["positive"])
        c3.metric("중립", summary["neutral"])
        c4.metric("부정", summary["negative"])

        st.write(f"**종합 판단:** {summary['overall_label']}")

        # -------------------------------
        # 감성 분포
        # -------------------------------
        st.subheader("감성 라벨 분포")
        label_counts = (
            analyzed_df["sentiment_label"]
            .value_counts()
            .reindex(["긍정", "중립", "부정"], fill_value=0)
        )
        st.bar_chart(label_counts)

        # -------------------------------
        # 상세 테이블
        # -------------------------------
        st.subheader("기사별 감성 분석 상세")

        display_cols = []
        for col in ["date", "source", "title", "sentiment_score", "sentiment_label", "positive_hits", "negative_hits", "link"]:
            if col in analyzed_df.columns:
                display_cols.append(col)

        st.dataframe(
            analyzed_df[display_cols],
            use_container_width=True,
            hide_index=True,
        )

        # -------------------------------
        # 긍정 / 부정 뉴스 따로 보기
        # -------------------------------
        st.subheader("감성별 뉴스 보기")

        tab1, tab2, tab3 = st.tabs(["긍정 뉴스", "중립 뉴스", "부정 뉴스"])

        with tab1:
            pos_df = analyzed_df[analyzed_df["sentiment_label"] == "긍정"].copy()
            if pos_df.empty:
                st.info("긍정 뉴스가 없습니다.")
            else:
                st.dataframe(pos_df[display_cols], use_container_width=True, hide_index=True)

        with tab2:
            neu_df = analyzed_df[analyzed_df["sentiment_label"] == "중립"].copy()
            if neu_df.empty:
                st.info("중립 뉴스가 없습니다.")
            else:
                st.dataframe(neu_df[display_cols], use_container_width=True, hide_index=True)

        with tab3:
            neg_df = analyzed_df[analyzed_df["sentiment_label"] == "부정"].copy()
            if neg_df.empty:
                st.info("부정 뉴스가 없습니다.")
            else:
                st.dataframe(neg_df[display_cols], use_container_width=True, hide_index=True)

        # -------------------------------
        # 디버깅용 확인
        # -------------------------------
        with st.expander("디버깅 정보 보기"):
            st.write("라벨 분포")
            st.write(analyzed_df["sentiment_label"].value_counts())

            st.write("점수 통계")
            st.write(analyzed_df["sentiment_score"].describe())

            st.write("원본 데이터 미리보기")
            st.dataframe(news_df.head(10), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"감성 분석 중 오류가 발생했습니다: {e}")

else:
    st.info("왼쪽 사이드바에서 조건을 입력하고 **감성 분석 실행** 버튼을 눌러주세요.")