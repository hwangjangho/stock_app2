from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict

import pandas as pd


@dataclass
class SentimentResult:
    label: str
    score: float
    positive_hits: List[str]
    negative_hits: List[str]
    normalized_text: str


POSITIVE_PATTERNS: Dict[str, float] = {
    "급등": 2.5,
    "상승": 1.8,
    "반등": 1.8,
    "강세": 1.6,
    "호재": 2.2,
    "호실적": 2.4,
    "실적 개선": 2.2,
    "개선": 1.2,
    "증가": 1.2,
    "성장": 1.5,
    "확대": 1.1,
    "회복": 1.8,
    "흑자": 2.4,
    "흑자전환": 2.8,
    "기대": 1.0,
    "기대감": 1.4,
    "수혜": 2.0,
    "돌파": 1.8,
    "최대": 1.0,
    "신고가": 2.3,
    "매수": 1.3,
    "추천": 0.8,
    "계약 체결": 2.0,
    "수주": 2.1,
    "수주 성공": 2.5,
    "배당 확대": 2.0,
    "턴어라운드": 2.2,
    "사상 최대": 2.8,
    "실적 성장": 2.3,
    "매출 증가": 2.0,
    "영업이익 증가": 2.3,
    "저평가": 1.5,
}

NEGATIVE_PATTERNS: Dict[str, float] = {
    "급락": -2.8,
    "하락": -1.8,
    "약세": -1.5,
    "악재": -2.3,
    "실적 부진": -2.4,
    "부진": -1.8,
    "감소": -1.2,
    "역성장": -2.2,
    "둔화": -1.6,
    "우려": -1.5,
    "쇼크": -2.6,
    "적자": -2.5,
    "적자전환": -2.8,
    "손실": -2.2,
    "축소": -1.2,
    "리스크": -1.8,
    "하향": -1.6,
    "매도": -1.2,
    "신저가": -2.3,
    "실망": -2.0,
    "불확실성": -1.5,
    "지연": -1.2,
    "중단": -1.8,
    "충격": -2.0,
    "급감": -2.3,
    "영업손실": -2.6,
    "매출 감소": -2.0,
    "어닝쇼크": -2.8,
    "비용 증가": -1.5,
    "수요 둔화": -2.0,
}

NEUTRALIZE_PATTERNS = [
    ("우려 완화", 1.5),
    ("적자 폭 축소", 1.8),
    ("손실 축소", 1.8),
    ("하락 제한", 1.0),
    ("부진 탈출", 2.0),
    ("실적 개선", 2.0),
    ("우려 해소", 2.0),
    ("반등 성공", 2.2),
]

BOOSTER_PATTERNS = {
    "사상 최대": 1.5,
    "큰 폭": 1.0,
    "대폭": 1.2,
    "뚜렷": 0.8,
    "본격화": 0.8,
    "예상 상회": 1.8,
    "시장 기대치 상회": 2.2,
    "예상 하회": -1.8,
    "시장 기대치 하회": -2.2,
}


def normalize_korean_finance_text(text: str) -> str:
    if text is None:
        return ""

    text = str(text).strip()
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\"'“”‘’$$$$$$$$]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _collect_pattern_hits(text: str, patterns: Dict[str, float]):
    hits = []
    score = 0.0

    for pattern, value in patterns.items():
        if pattern in text:
            hits.append(pattern)
            score += value

    return hits, score


def _apply_neutralize_patterns(text: str, base_score: float) -> float:
    score = base_score
    for pattern, value in NEUTRALIZE_PATTERNS:
        if pattern in text:
            score += value
    return score


def _apply_boosters(text: str, base_score: float) -> float:
    score = base_score
    for pattern, value in BOOSTER_PATTERNS.items():
        if pattern in text:
            score += value
    return score


def _length_normalize(score: float, text: str) -> float:
    length = max(len(text), 10)
    norm = min(1.15, max(0.85, 30 / length))
    return score * norm


def classify_sentiment(score: float) -> str:
    if score >= 1.2:
        return "긍정"
    elif score <= -1.2:
        return "부정"
    else:
        return "중립"


def analyze_sentiment(text: str) -> SentimentResult:
    normalized = normalize_korean_finance_text(text)

    if not normalized:
        return SentimentResult(
            label="중립",
            score=0.0,
            positive_hits=[],
            negative_hits=[],
            normalized_text="",
        )

    positive_hits, pos_score = _collect_pattern_hits(normalized, POSITIVE_PATTERNS)
    negative_hits, neg_score = _collect_pattern_hits(normalized, NEGATIVE_PATTERNS)

    total_score = pos_score + neg_score
    total_score = _apply_neutralize_patterns(normalized, total_score)
    total_score = _apply_boosters(normalized, total_score)
    total_score = _length_normalize(total_score, normalized)

    label = classify_sentiment(total_score)

    return SentimentResult(
        label=label,
        score=round(total_score, 4),
        positive_hits=positive_hits,
        negative_hits=negative_hits,
        normalized_text=normalized,
    )


def apply_sentiment_to_df(df: pd.DataFrame, text_col: str = "title") -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()

    if df.empty:
        out = df.copy()
        if "sentiment_score" not in out.columns:
            out["sentiment_score"] = []
        if "sentiment_label" not in out.columns:
            out["sentiment_label"] = []
        if "positive_hits" not in out.columns:
            out["positive_hits"] = []
        if "negative_hits" not in out.columns:
            out["negative_hits"] = []
        return out

    if text_col not in df.columns:
        raise ValueError(f"'{text_col}' 컬럼이 dataframe에 없습니다.")

    out = df.copy()

    scores = []
    labels = []
    positive_hits_all = []
    negative_hits_all = []

    for text in out[text_col].fillna(""):
        result = analyze_sentiment(text)
        scores.append(result.score)
        labels.append(result.label)
        positive_hits_all.append(", ".join(result.positive_hits))
        negative_hits_all.append(", ".join(result.negative_hits))

    out["sentiment_score"] = scores
    out["sentiment_label"] = labels
    out["positive_hits"] = positive_hits_all
    out["negative_hits"] = negative_hits_all

    return out


def summarize_sentiment(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {
            "avg_score": 0.0,
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "overall_label": "중립",
        }

    positive = int((df["sentiment_label"] == "긍정").sum())
    neutral = int((df["sentiment_label"] == "중립").sum())
    negative = int((df["sentiment_label"] == "부정").sum())
    avg_score = round(float(df["sentiment_score"].mean()), 4)

    if avg_score >= 0.5:
        overall = "전반적으로 긍정"
    elif avg_score <= -0.5:
        overall = "전반적으로 부정"
    else:
        overall = "혼조/중립"

    return {
        "avg_score": avg_score,
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "overall_label": overall,
    }