from __future__ import annotations

import json
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()


def summarize_news_korean(rows: List[Dict[str, Any]]) -> str:
    """
    rows 예시:
    [
      {"title": "...", "label": "positive", "score": 0.7, "reason": "..."},
      ...
    ]
    """
    if not rows:
        return "분석할 뉴스 데이터가 없습니다."

    payload = [
        {
            "title": r.get("title", ""),
            "label": r.get("label", ""),
            "score": r.get("score", 0.0),
            "reason": r.get("reason", ""),
            "source": r.get("source", ""),
        }
        for r in rows
    ]

    prompt = f"""
다음은 여러 뉴스 기사에 대한 감성분석 결과이다.
이 결과를 바탕으로 한국어로 간결하게 요약하라.

요구사항:
1. 전체 분위기가 긍정/중립/부정 중 어디에 가까운지 설명
2. 주요 이유를 3가지 이내로 정리
3. 투자자가 참고할 만한 시사점을 한두 문장으로 작성
4. 반드시 한국어로 작성
5. 너무 길지 않게 작성

데이터:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": "당신은 금융 뉴스 감성분석 결과를 한국어로 요약하는 도우미다."},
            {"role": "user", "content": prompt},
        ],
    )

    return resp.choices[0].message.content.strip()


def summarize_financials_korean(financial_data: Dict[str, Any]) -> str:
    """
    financial_data 예시:
    {
      "revenue": ...,
      "operating_income": ...,
      "net_income": ...,
      "assets": ...,
      "liabilities": ...,
      "equity": ...,
      "comment": ...
    }
    """
    if not financial_data:
        return "요약할 재무제표 데이터가 없습니다."

    prompt = f"""
다음은 기업의 재무제표 또는 재무지표 분석 결과이다.
이 데이터를 바탕으로 한국어로 이해하기 쉽게 요약하라.

요구사항:
1. 매출, 이익, 자산/부채, 전반적 재무건전성을 중심으로 설명
2. 긍정적인 점과 주의할 점을 함께 작성
3. 숫자를 그대로 반복하지 말고 의미를 해석해서 설명
4. 반드시 한국어로 작성
5. 5문장 이내로 간결하게 작성

데이터:
{json.dumps(financial_data, ensure_ascii=False, indent=2)}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": "당신은 기업 재무제표 분석 결과를 한국어로 요약하는 도우미다."},
            {"role": "user", "content": prompt},
        ],
    )

    return resp.choices[0].message.content.strip()


def summarize_overall_korean(
    news_summary: str,
    financial_summary: str,
) -> str:
    prompt = f"""
다음 두 개의 요약을 바탕으로 투자 관점의 종합 의견을 한국어로 작성하라.

[뉴스 감성 요약]
{news_summary}

[재무제표 요약]
{financial_summary}

요구사항:
1. 뉴스 흐름과 재무상태를 함께 고려
2. 종합적으로 긍정/중립/주의 중 어느 쪽인지 설명
3. 과장 없이 현실적으로 작성
4. 반드시 한국어로 작성
5. 4문장 이내
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        messages=[
            {"role": "system", "content": "당신은 투자 참고용 종합 코멘트를 한국어로 작성하는 도우미다."},
            {"role": "user", "content": prompt},
        ],
    )

    return resp.choices[0].message.content.strip()

