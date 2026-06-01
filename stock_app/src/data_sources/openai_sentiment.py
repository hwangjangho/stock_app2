# src/data_sources/openai_sentiment.py
from __future__ import annotations

import json
import re
import time

from openai import OpenAI


client = OpenAI()


def _extract_json(text: str) -> dict:
    text = (text or "").strip()

    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except Exception:
        pass

    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass

    return {"label": "neutral", "score": 0.0, "reason": "parse failed"}


def sentiment_score(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {"label": "neutral", "score": 0.0, "reason": "empty text"}

    prompt = f"""
다음 뉴스 텍스트의 감성을 분석해줘.
반드시 JSON만 출력해.

형식:
{{
  "label": "positive | neutral | negative",
  "score": -1.0,
  "reason": "한 줄 설명"
}}

텍스트:
{text[:800]}
""".strip()

    last_error = None

    for wait in [1, 2, 4]:
        try:
            resp = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
            )

            output_text = getattr(resp, "output_text", None)

            if not output_text:
                try:
                    output_text = resp.output[0].content[0].text
                except Exception:
                    output_text = str(resp)

            data = _extract_json(output_text)

            label = str(data.get("label", "neutral")).strip().lower()
            if label not in {"positive", "neutral", "negative"}:
                label = "neutral"

            try:
                score = float(data.get("score", 0.0))
            except Exception:
                score = 0.0

            reason = str(data.get("reason", "")).strip()

            return {
                "label": label,
                "score": score,
                "reason": reason,
            }

        except Exception as e:
            last_error = e
            if "429" in str(e):
                time.sleep(wait)
                continue
            break

    return {
        "label": "neutral",
        "score": 0.0,
        "reason": f"OpenAI API failed: {last_error}",
    }