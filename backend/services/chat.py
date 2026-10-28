import json

from fastapi import HTTPException
from openai import OpenAI

from backend.config import Settings


def build_system_prompt(summary: dict) -> str:
    return f"""당신은 사용자의 시계열 데이터를 이해하는 친절하고 정확한 데이터 분석 비서입니다.

[사용자 데이터 요약]
- 데이터 기간: {summary['period']}
- 총 레코드: {summary['count']}개
- 주요 지표: {json.dumps(summary['metrics'], ensure_ascii=False)}
- 최근 트렌드: {summary['trend']}
- 최신 데이터: {json.dumps(summary['latest'], ensure_ascii=False)}

반드시 제공된 데이터에 근거해 한국어로 답하세요. 데이터만으로 알 수 없는 내용은 추측하지 말고 한계를 밝혀 주세요.
금액 단위는 데이터에 명시되지 않았으므로 사용자가 단위를 말하지 않았다면 임의로 정하지 마세요.
답변은 핵심 결론과 근거 수치를 포함해 5문장 이내로 작성하세요."""


def ask_openai(settings: Settings, summary: dict, history: list[dict], question: str) -> str:
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY가 설정되지 않았습니다.")

    client = OpenAI(api_key=settings.openai_api_key)
    messages = [{"role": "system", "content": build_system_prompt(summary)}]
    messages.extend(history[-20:])
    messages.append({"role": "user", "content": question})
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )
        return response.choices[0].message.content or "답변을 생성하지 못했습니다."
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI 서비스 호출에 실패했습니다.") from exc

