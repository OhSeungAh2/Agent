# /meating
# /summarize

# pip install fastapi
# pip install uvicorn

# 실행방법: uvicorn fastapi_back:app --reload --port 8000

import uuid
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from graph import run_meeting_pipeline
from db import (init_db, list_meetings, format_meetings_markdown, get_meeting)
from asr import asr_status, transcribe_file

# 업로드된 파일을 저장할 디렉토리 설정
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# FastAPI 앱의 수명 주기 관리 (lifespan) 정의
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

# 업로드된 파일을 서버에 저장하는 내부 함수
def _save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return dest


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

# FastAPI 엔드포인트: ASR 상태 확인
@app.get("/meetings")
def meetings_list(limit: int = 10):
    # list_meetings : 이건 db.py에 정의되어 있어야 함
    rows = list_meetings(limit=limit)
    return {
        "items": rows,
        "markdown": format_meetings_markdown(rows),
        "result": format_meetings_markdown(rows)
    }

# FastAPI 엔드포인트: 특정 회의 상세 정보 확인
@app.get("/meetings/{meeting_id}")
def meetings_detail(meeting_id: int):
    # get_meeting : 이건 db.py에 정의되어 있어야 함
    row = get_meeting(meeting_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"회의 #{meeting_id}를 찾을 수 없습니다.")
    detail = format_meetings_markdown(row)
    return {"item": row, "markdown": detail, "result": detail}


@app.get("/asr/status")
def get_asr_status():
    return asr_status()

@app.post("/transcribe")
async def transcribe_only(file: UploadFile = File(...)):
    path = _save_upload(file)
    try:
        tr = transcribe_file(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "text": tr.text,
        "mode": tr.mode,
        "rms": tr.rms,
        "peak": tr.peak,
        "skipped_silence": tr.skipped_silence,
        "detail": tr.detail,
        "result": (
            f"### 전사 결과\n\n"
            f"- 모드: `{tr.mode}`\n"
            f"- RMS: `{tr.rms:.4f}` / peak: `{tr.peak:.4f}`\n"
            f"- {tr.detail}\n\n"
            f"```\n{tr.text or '(빈 결과)'}\n```"
        ),
        "markdown": (
            f"### 전사 결과\n\n"
            f"- 모드: `{tr.mode}`\n"
            f"- RMS: `{tr.rms:.4f}` / peak: `{tr.peak:.4f}`\n"
            f"- {tr.detail}\n\n"
            f"```\n{tr.text or '(빈 결과)'}\n```"
        ),
    }

@app.post("/pipline_audio")
async def run_pipeline_audio(
    title: str = Form(...),
    people: str = Form(""),
    file: UploadFile = File(...)
):
    path = _save_upload(file)
    # ...
