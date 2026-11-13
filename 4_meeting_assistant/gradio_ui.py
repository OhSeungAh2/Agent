
# pip install gradio

# 실행 방법: python gradio_ui.py

import gradio as gr
import requests
from pathlib import Path

API_URL = "http://127.0.0.1:8000" 

# API 호출 함수 : 이걸로 공통으로 사용하면서 아래 함수가 정리됨! (git commit 참고해서 비교하기)
def call_api(path: str, payload: dict | None = None, method: str = "POST") -> str:
    try:
        url = f"{API_URL}{path}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=payload or {}, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "markdown" in data:
            return data["markdown"]
        if "result" in data:
            text = data["result"]
            meeting_id = data.get("meeting_id") or 0
            if meeting_id:
                text += f"\n\n_(응답 meeting_id={meeting_id})_"
            return text
        return str(data)
    except(requests.RequestException, ValueError, KeyError) as e:
        return f"서버 통신 오류: {e}"


# FastAPI 서버와 통신하는 함수 정의
def make_meeting(title: str, people: str) -> str:
    return call_api("/meeting", {"title": title, "people": people})

# Gradio UI와 연결할 함수 정의
def summarize(text: str) -> str:
    return call_api("/summarize", {"text": text})

# 전체 파이프라인 실행 함수 정의
def run_pipeline(title: str, people: str, notes: str) -> str:
    return call_api("/pipeline", {"title": title, "people": people, "notes": notes})

# 저장된 회의 조회 함수 정의
def show_meetings() -> str:
    return call_api("/meetings", method="GET")

# ASR 상태 조회 함수 정의
def show_asr_status() -> str:
    return call_api("/asr/status", method="GET")

# 특정 회의 상세 조회 함수 정의
def show_meeting_detail(meeting_id: float | int) -> str:
    try:
        mid = int(meeting_id)
    except (TypeError, ValueError):
        return "조회할 회의 id를 숫자로 입력해주세요."
    if mid <= 0:
        return "1 이상의 회의 id를 입력하세요."
    return call_api(f"/meetings/{mid}", method="GET")

# 오디오 입력(audio)을 파일 경로(path)로 변환하는 함수
def _audio_to_path(audio) -> str | None:
    if audio is None:
        return None
    if isinstance(audio, str) and audio:
        return audio
    if isinstance(audio, dict):
        for key in ("path", "name"):
            if audio.get(key):
                return str(audio[key])
    if isinstance(audio, (list, tuple)) and audio and isinstance(audio[0], str):
        return audio[0]
    return None

# 오디오 전사 함수 정의
# 전사란? 음성을 텍스트로 변환하는 과정
def transcribe_audio(audio) -> str:
    path = _audio_to_path(audio)
    if not path or not Path(path).is_file():
        return "음성 파일 or 마이크 녹음을 먼저 입력하세요."
    try:
        # rb란 읽기 모드(read) + 바이너리 모드(binary)
        # b말고 t로 쓰면 텍스트 모드로 열림
        with open(path, "rb") as f:
            response = requests.post(
                f"{API_URL}/transcribe",
                files={"file": (Path(path).name, f, "application/octet-stream")},
                timeout=100
            )
        response.raise_for_status()
        data = response.json()
        return data.get("markdown") or data.get("result") or str(data)
    except(requests.RequestException, ValueError, KeyError) as e:
        return f"서버 통신 오류: {e}"

# 오디오 기반 전체 파이프라인 실행 함수 정의
def run_audio_pipeline(title:str, people:str, audio) -> str:
    path = _audio_to_path(audio)
    if not path or not Path(path).is_file():
        return "음성 파일 or 마이크 녹음을 먼저 입력하세요."
    if not (title or "").strip():
        return "제목을 입력하세요."
    try:
        with open(path, "rb") as f:
            response = requests.post(
                f"{API_URL}/pipeline_audio",
                data = {"title": title, "people": people or ""},
                files={"file": (Path(path).name, f, "application/octet-stream")},
                timeout=100
            )
        response.raise_for_status()
        data = response.json()
        text = data.get("result") or str(data)
        meeting_id = data.get("meeting_id") or 0
        if meeting_id:
            text += f"\n\n_(응답 meeting_id={meeting_id})_"
        return text
    except(requests.RequestException, ValueError, KeyError) as e:
        return f"서버 통신 오류: {e}"

# Gradio UI 구성
with gr.Blocks(title="Gradio Tabs 예제") as demo:
    gr.Markdown("# Gradio + FastAPI 예제\nFastAPI 서버와 통신하는 Gradio UI입니다.")

    # 탭 1
    with gr.Tab("1. 회의 생성"):
        title = gr.Textbox(label="제목", value="주간 회의")
        people = gr.Textbox(label="참가자(쉼표)", value="김사과, 이메론")
        btn1 = gr.Button("생성", variant="primary")
        out1 = gr.Markdown()
        # 버튼과 함수 연결
        btn1.click(make_meeting, inputs=[title, people], outputs=out1)

    # 탭 2
    with gr.Tab("2. 간단 요약"):
        raw = gr.Textbox(label="회의록", lines=6, value="김사과: 목표공유\n이메론: API 완료예정")
        btn2 = gr.Button("요약")
        out2 = gr.Markdown()
        # 버튼과 함수 연결
        btn2.click(summarize, inputs=[raw], outputs=out2)

    # 탭 3 = 전체 파이프라인(탭1, 탭2)
    with gr.Tab("3. 전체 파이프라인"):
        gr.Markdown("한 번에 검증 > 회의 생성 > 요약 > 엑션추출 > 결과조합을 실행")
        p_title = gr.Textbox(label="제목", value="주간 회의")
        p_people = gr.Textbox(label="참가자(쉼표)", value="김사과, 이메론")
        p_notes = gr.Textbox(label="회의록", lines=6, value="김사과: 목표공유\n이메론: API 완료예정")
        btn3 = gr.Button("파이프라인 실행", variant="primary")
        out3 = gr.Markdown()
        # 버튼과 함수 연결
        btn3.click(run_pipeline, inputs=[p_title, p_people, p_notes], outputs=out3)
    
    # 탭 4
    with gr.Tab("4. 저장된 회의"):
        gr.Markdown("저장된 결과를 조회합니다.")
        btn4 = gr.Button("목록 새로고침")
        out4 = gr.Markdown()
        # 버튼과 함수 연결
        btn4.click(show_meetings, outputs=out4)

        mid = gr.Number(label="회의 id", value=1, precision=0)
        btn5 = gr.Button("상세 조회")
        out5 = gr.Markdown()
        btn5.click(show_meeting_detail, inputs=mid, outputs=out5)

    # 탭 5 = 음성 인식 실습
    with gr.Tab("5. 음성 회의"):
        gr.Markdown(
            "마이크 녹음 or wav 업로드 → 전처리 → 전사 → 기존 LangGraph 파이프라인 → DB 저장"
        )
        btn_status = gr.Button("ASR 상태 조회")
        out_status = gr.Markdown()
        btn_status.click(show_asr_status, outputs=out_status)

        audio = gr.Audio(
            label="마이크 녹음 또는 파일",
            sources=["microphone", "upload"],
            type="filepath"
        )
        a_title = gr.Textbox(label="제목", value="음성 주간 회의")
        a_people = gr.Textbox(label="참가자(쉼표)", value="김사과, 이메론")
        btn_tr = gr.Button("전사만 실행 (/transcribe)")
        out_tr = gr.Markdown()
        btn_tr.click(transcribe_audio, inputs=audio, outputs=out_tr)

        btn_pipe = gr.Button("음성 파이프라인 실행", variant="primary")
        out_pipe = gr.Markdown()
        btn_pipe.click(
            run_audio_pipeline, inputs=[a_title, a_people, audio], outputs=out_pipe
        )


# 화면 실행
# __name__ == "__main__" 체크 후 실행(무엇을 체크하냐 = 현재 파일이 메인으로 실행되는지 여부)
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=9999)

