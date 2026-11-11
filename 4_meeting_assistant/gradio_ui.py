
# pip install gradio

# 실행 방법: python gradio_ui.py

import gradio as gr
import requests

API_URL = "http://127.0.0.1:8000" 

# API 호출 함수 : 이걸로 공통으로 사용하면서 아래 함수가 정리됨! (git commit 참고해서 비교하기)
def call_api(path: str, payload: dict) -> str:
    try:
        response = requests.post(f"{API_URL}{path}", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()["result"]
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
        gr.Markdown("저장된 회의를 확인합니다.")
        btn4 = gr.Button("목록 새로고침")
        out4 = gr.Markdown()
        # 버튼과 함수 연결
        # btn4.click(show_meetings, outputs=out4)

        mid = gr.Number(label="회의 ID", value=1, precision=0)
        btn5 = gr.Button("회의 상세보기")
        out5 = gr.Markdown()
        # btn5.click(show_meeting_detail, inputs=mid, outputs=out5)
    

# 화면 실행
# __name__ == "__main__" 체크 후 실행(무엇을 체크하냐 = 현재 파일이 메인으로 실행되는지 여부)
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=9999)

