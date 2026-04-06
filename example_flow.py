"""
LangFlow 예제: lot_id / eqp_id 조회 Q&A 시스템
----------------------------------------------
실제 사내 환경에 적용할 때:
  - BASE_URL → 사내 LLM 엔드포인트
  - API_KEY  → 사내 API 키
  - call_lot_api() / call_eqp_api() → 실제 사내 API로 교체
"""

import json
import requests

# ── 설정 (사내 환경에 맞게 변경) ─────────────────────────────────────────────
LLM_BASE_URL = "https://api.openai.com/v1"          # 사내: http://내부IP:포트/v1
LLM_API_KEY  = "sk-YOUR-KEY"                         # 사내 API Key
LLM_MODEL    = "gpt-4o-mini"                         # 사내: gpt-oss-120b / kimi 등
# ─────────────────────────────────────────────────────────────────────────────


# ── Step 1: LLM으로 질문에서 lot_id / eqp_id 추출 ────────────────────────────
EXTRACT_PROMPT = """
너는 반도체 제조 시스템 어시스턴트야.
사용자 질문에서 아래 정보를 추출해서 반드시 JSON만 반환해. 설명 없이 JSON만.

추출 항목:
- type: "lot" 또는 "eqp" (둘 다 없으면 "unknown")
- id: 추출한 ID 값 (없으면 null)
- intent: 질문 의도 ("status" / "history" / "alarm" / "location" / "yield" / "other")

예시 입력: "LOT-20240101 지금 어느 공정이야?"
예시 출력: {{"type": "lot", "id": "LOT-20240101", "intent": "location"}}

예시 입력: "CVD-03 장비 최근 알람 알려줘"
예시 출력: {{"type": "eqp", "id": "CVD-03", "intent": "alarm"}}

사용자 질문: {user_input}
"""

def extract_entity(user_input: str) -> dict:
    """LLM을 호출해서 lot_id 또는 eqp_id를 추출한다."""
    prompt = EXTRACT_PROMPT.format(user_input=user_input)

    response = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,           # 추출은 일관성이 중요하므로 0
        },
    )
    response.raise_for_status()

    raw = response.json()["choices"][0]["message"]["content"].strip()

    # LLM이 ```json ... ``` 으로 감쌀 수도 있으므로 방어 처리
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)


# ── Step 2: 사내 API 호출 (Mock → 실제 API로 교체) ───────────────────────────
def call_lot_api(lot_id: str, intent: str) -> dict:
    """
    실제 사내 API 예시:
        GET http://mes-api.internal/lot/{lot_id}/{intent}
    """
    # ── Mock 데이터 (실제 API 연동 시 아래를 교체) ──
    mock_db = {
        "LOT-20240101": {
            "status":   {"stage": "CVD", "equipment": "CVD-03", "progress": "85%"},
            "history":  {"steps_done": ["DIFF", "OXIDE", "CVD"], "current": "CVD"},
            "alarm":    {"count": 0, "last": None},
            "location": {"fab": "FAB-2", "bay": "BAY-3", "equipment": "CVD-03"},
            "yield":    {"target": "98%", "current": "97.2%"},
        }
    }
    data = mock_db.get(lot_id, {}).get(intent, {"message": "데이터 없음"})
    return {"lot_id": lot_id, "intent": intent, "data": data}


def call_eqp_api(eqp_id: str, intent: str) -> dict:
    """
    실제 사내 API 예시:
        GET http://mes-api.internal/equipment/{eqp_id}/{intent}
    """
    # ── Mock 데이터 (실제 API 연동 시 아래를 교체) ──
    mock_db = {
        "CVD-03": {
            "status":   {"state": "RUN", "recipe": "CVD_OXIDE_V3", "wafer_count": 25},
            "history":  {"last_pm": "2024-03-15", "total_run": 1423},
            "alarm":    {"count": 3, "last": "2024-04-01 14:32", "code": "TEMP_HIGH"},
            "location": {"fab": "FAB-2", "bay": "BAY-3", "chamber": "CH-A"},
            "yield":    {"avg_yield": "96.8%", "period": "최근 30일"},
        }
    }
    data = mock_db.get(eqp_id, {}).get(intent, {"message": "데이터 없음"})
    return {"eqp_id": eqp_id, "intent": intent, "data": data}


# ── Step 3: LLM으로 API 결과를 자연어 답변으로 변환 ──────────────────────────
ANSWER_PROMPT = """
너는 반도체 제조 현장의 친절한 MES 어시스턴트야.
아래 데이터를 바탕으로 사용자 질문에 한국어로 간결하게 답변해줘.

사용자 질문: {user_input}
조회 결과: {api_result}

- 핵심 정보를 먼저 말하고, 필요한 경우 세부 사항을 덧붙여줘.
- 데이터가 없으면 "해당 정보를 찾을 수 없습니다"라고 안내해줘.
"""

def generate_answer(user_input: str, api_result: dict) -> str:
    """API 결과를 자연어 답변으로 변환한다."""
    prompt = ANSWER_PROMPT.format(
        user_input=user_input,
        api_result=json.dumps(api_result, ensure_ascii=False, indent=2),
    )

    response = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        },
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


# ── 전체 파이프라인 ───────────────────────────────────────────────────────────
def run_pipeline(user_input: str) -> str:
    print(f"\n질문: {user_input}")

    # Step 1: Entity 추출
    entity = extract_entity(user_input)
    print(f"추출 결과: {entity}")

    if entity["type"] == "unknown" or entity["id"] is None:
        return "lot_id 또는 eqp_id를 찾을 수 없습니다. 다시 질문해주세요."

    # Step 2: 사내 API 호출
    if entity["type"] == "lot":
        api_result = call_lot_api(entity["id"], entity["intent"])
    else:
        api_result = call_eqp_api(entity["id"], entity["intent"])
    print(f"API 결과: {api_result}")

    # Step 3: 자연어 답변 생성
    answer = generate_answer(user_input, api_result)
    print(f"답변: {answer}\n")
    return answer


# ── 테스트 실행 ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_questions = [
        "LOT-20240101 지금 어느 공정이야?",
        "CVD-03 장비 최근 알람 알려줘",
        "LOT-20240101 수율이 어떻게 돼?",
        "CVD-03 마지막 PM이 언제야?",
    ]

    for q in test_questions:
        run_pipeline(q)
