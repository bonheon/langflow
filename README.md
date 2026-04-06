# LangFlow - Lot / Eqp Query System

## 파일 구조

```
LangFlow/
├── example_flow.py      # Python으로 전체 로직 확인 (로컬 테스트용)
├── lot_eqp_flow.json    # LangFlow에 import할 Flow 파일
└── README.md
```

## 사내 적용 시 변경 항목

### 1. LLM 엔드포인트 (2곳)
`lot_eqp_flow.json` 및 `example_flow.py`에서:
```
"http://YOUR-INTERNAL-LLM-HOST/v1"  →  실제 사내 LLM 주소
"YOUR-API-KEY"                       →  실제 API Key
"gpt-oss-120b"                       →  실제 모델명 (kimi, gvm 등)
```

### 2. 사내 API 연동 (apiCaller 컴포넌트)
`lot_eqp_flow.json`의 `apiCaller` 코드에서 Mock 데이터 부분을 실제 API 호출로 교체:
```python
# 이 부분을 교체
response = requests.get(
    f"http://mes-api.internal/{id_type}/{id_value}/{intent}",
    headers={"Authorization": "Bearer YOUR-MES-KEY"},
    timeout=10
)
api_data = response.json()
```

## LangFlow에서 import 방법
1. LangFlow 접속
2. 우측 상단 "Upload" 또는 "Import" 버튼 클릭
3. `lot_eqp_flow.json` 파일 선택

## Flow 구조

```
[Chat Input]
    ↓
[Entity Extractor Prompt]  ← lot_id / eqp_id 추출 프롬프트
    ↓
[LLM - Extract]            ← temperature=0 (일관된 JSON 출력)
    ↓
[API Caller]               ← 사내 API 호출 (Python 코드)
    ↓
[Answer Generator Prompt]  ← API 결과 + 원래 질문
    ↓
[LLM - Answer]             ← temperature=0.3 (자연스러운 답변)
    ↓
[Chat Output]
```

## 향후 기능 추가 방법
- API Caller 코드에 intent 케이스 추가
- 필요 시 Router 노드로 lot / eqp 경로를 분기
- 새 기능 = 새 Tool / 새 API endpoint 추가
