# /meating
# /summarize

# pip install fastapi
# pip install uvicorn

# 실행방법: uvicorn fastapi_back:app --reload --port 8000

from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from graph import run_meeting_pipeline
from db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # db 초기화 시작
    init_db()
    # db 초기화 완료 후 앱 실행
    yield


app = FastAPI(title="회의 관리 API", lifespan=lifespan)

# 요청 데이터 모델 정의
class MeetingRequest(BaseModel):
    title: str
    people: str

# 요약 관련 요청 데이터 모델 정의
class SummaryRequest(BaseModel):
    text: str

# 전체 파이프라인 관련 요청 데이터 모델 정의
class PipelineRequest(BaseModel):
    title: str
    people: str
    notes: str


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

# FastAPI 엔드포인트: 전체 파이프라인 실행
@app.post("/pipeline")
def run_pipeline(request: PipelineRequest):
    # 그래프에서 함수 만들어서 그 함수를 받아 처리하는 방법으로 만들거임
    return {
        "result": run_meeting_pipeline(
            title = request.title,
            people = request.people,
            notes = request.notes
        )
    }