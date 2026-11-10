
# pip install gradio

# 실행 방법: python 4_gradio.py

import gradio as gr
import requests

API_URL = "http://127.0.0.1:8000" 

# FastAPI 서버와 통신하는 함수 정의
def make_meeting(title: str, people: str) -> str:
    try:
        response = requests.post(f"{API_URL}/meeting", json={"title": title, "people": people})
        response.raise_for_status()
        return response.json()["result"]
    except(requests.RequestException, ValueError, KeyError) as e:
        return f"서버 통신 오류: {e}"

# Gradio UI와 연결할 함수 정의
def summarize(text: str) -> str:
    try:
        response = requests.post(f"{API_URL}/summarize", json={"text": text})
        response.raise_for_status()
        return response.json()["result"]
    except(requests.RequestException, ValueError, KeyError) as e:
        return f"서버 통신 오류: {e}"

# Gradio UI 구성
with gr.Blocks(title="Gradio Tabs 예제") as demo:
    gr.Markdown("# Gradio + FastAPI 예제\nFastAPI 서버와 통신하는 Gradio UI입니다.")

    # 탭 구성
    with gr.Tab("1. 회의 생성"):
        title = gr.Textbox(label="제목", value="주간 회의")
        people = gr.Textbox(label="참가자(쉼표)", value="김사과, 이메론")
        btn1 = gr.Button("생성", variant="primary")
        out1 = gr.Markdown()
        # 버튼과 함수 연결
        btn1.click(make_meeting, inputs=[title, people], outputs=out1)
    with gr.Tab("2. 간단 요약"):
        raw = gr.Textbox(label="회의록", lines=6, value="회의 내용을 입력하세요.")
        btn2 = gr.Button("요약")
        out2 = gr.Markdown()
        # 버튼과 함수 연결
        btn2.click(summarize, inputs=[raw], outputs=out2)
    # 탭3 = 전체 파이프라인(탭1, 탭2)

# 화면 실행
# __name__ == "__main__" 체크 후 실행(무엇을 체크하냐 = 현재 파일이 메인으로 실행되는지 여부)
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=9999)

