# /meating
# /summarize

# pip install fastapi
# pip install uvicorn

# 실행방법: uvicorn 4_fastapi:app --reload --port 8000

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="회의 관리 API")

class MeetingRequest(BaseModel):
    title: str
    people: str

class SummaryRequest(BaseModel):
    text: str

# 미팅 관련 함수
def make_meeting(title: str, people: str) -> str:
    title = (title or "").strip()
    if not title:
        return "제목을 입력하세요."
    names = [p.strip() for p in (people or "").split(",") if p.strip()]
    return (
        f"### 회의 생성됨\n"
        f"- 제목: {title}\n"
        f"- 참가자: {', '.join(names) or '없음'}"
    )

# 요약 관련 함수
def summarize(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return "회의록이 비어있습니다. 요약할 내용을 입력하세요."
    lines = [ln for ln in text.split("\n") if ln.strip()]
    return f"발화 {len(lines)}줄 요약 완료 / 앞부분: {lines[0] if lines else ''}"

# FastAPI 엔드포인트: 회의 생성 및 요약
@app.post("/meeting")
def create_meeting(request: MeetingRequest):
    return {"result": make_meeting(request.title, request.people)}

# FastAPI 엔드포인트: 회의 요약
@app.post("/summarize")
def create_summary(request: SummaryRequest):
    return {"result": summarize(request.text)}

# post/pipeline 탭3에서 온 데이터 받기 > 그리고 4_gradio.py로 보내서 처리
