# 그래프 그릴곳

# langGraph 예제: 주간 회의 도우미
# 노드1: 입력 검증
# 노드2: 회의 정보와 문구 생성(백엔드에서 만든 말 붙인것들)
# 노드3: 회의록 요약
# 노드4: 규칙
# 노드5: 최종 Markdown으로 조합해서 내보내기

# 내보내면 프론트가 받아서 화면에 표시함

from typing import TypedDict
from unittest import result
from langgraph.graph import StateGraph, START, END


# 회의 상태를 나타내는 TypedDict 정의
class MeetingState(TypedDict):
    title: str
    people: str
    notes: str
    error: str
    meeting_info: str
    summary: str
    actions: str
    result: str


# 첫번째 노드: 입력 검증
def validate_input(state: MeetingState) -> MeetingState:
    # or 앞이 True면 그대로 사용, False면 뒤의 값 사용
    title = (state.get("title") or "").strip() 
    notes = (state.get("notes") or "").strip()
    if not title:
        # **은 기존 state를 유지하면서 error만 덮어쓰는 방식
        return {**state, "error": "제목을 입력하세요."}
    if not notes:
        return {**state, "error": "회의록 내용을 입력하세요."}
    return {**state, "error": ""}

# 두번째 노드: 회의 정보 생성
def create_meeting(state: MeetingState) -> MeetingState:
    title = state["title"].strip()
    names = [p.strip() for p in (state.get("people") or "").split(",") if p.strip()]
    meeting_info = (
        f"### 회의 생성됨\n"
        f"- 제목: {title}\n"
        f"- 참가자: {', '.join(names) or '없음'}"
    )
    # 전부 다 복사해서~ meeting_info만 덮어쓰기
    return {**state, "meeting_info": meeting_info}

# 세번째 노드: 회의록 요약
def summarize_notes(state: MeetingState) -> MeetingState:
    # 회의록 내용을 줄 단위로 나누고 공백 제거
    lines = [ln.strip() for ln in state["notes"].splitlines() if ln.strip()]
    summary = f"발화 {len(lines)}줄 요약 완료 / 앞부분: {lines[0] if lines else ''}"
    return {**state, "summary": summary}

# 네번째 노드: 규칙 적용
def extract_actions(state: MeetingState) -> MeetingState:
    keywords = ("예정", "힐", "todo", "해야", "담당")
    found = []
    # splitlines: 각 줄을 확인하여 키워드가 포함된 줄을 found에 추가
    for line in state["notes"].splitlines():
        text = line.strip()
        if text and any(k in text.lower() for k in keywords):
            found.append(f"- {text}")
    actions = "\n".join(found) if found else "규칙에 맞는 행동 항목이 없습니다."
    return {**state, "actions": actions}

# 다섯번째 노드: 최종 Markdown으로 조합
def compose_result(state: MeetingState) -> MeetingState:
    if state.get("error"):
        return {**state, "result": f"### 오류발생\n{state['error']}"}
    result = (
        "### 회의 파이프라인 결과\n\n"
        f"1. 회의 정보\n{state['meeting_info']}\n\n"
        f"2. 회의록 요약\n{state['summary']}\n\n"
        f"3. 행동 항목\n{state['actions']}"
    )
    return {**state, "result": result}


# validate 노드 이후의 라우팅 함수 정의
# 쉽게 말해 validate 노드에서 에러가 있으면 "error"로, 없으면 "ok"로 이동하는 함수임
def route_after_validate(state: MeetingState) -> str:
    return "error" if state.get("error") else "ok"


# build_meeting_graph 함수: 그래프를 정의하는 함수임
def build_meeting_graph():
    graph = StateGraph(MeetingState)

    graph.add_node("validate", validate_input)
    graph.add_node("create_meeting", create_meeting)
    graph.add_node("summarize", summarize_notes)
    graph.add_node("extract_actions", extract_actions)
    graph.add_node("compose", compose_result)

    graph.add_edge(START, "validate")
    graph.add_conditional_edges(
        "validate", route_after_validate, {"ok": "create_meeting", "error": "compose"}
    )
    graph.add_edge("create_meeting", "summarize")
    graph.add_edge("summarize", "extract_actions")
    graph.add_edge("extract_actions", "compose")
    graph.add_edge("compose", END)

    return graph.compile()


# build_meeting_graph: state 그래프 만들어서 node 생성하고 edge 연결하는
meeting_app = build_meeting_graph()


def run_meeting_pipeline(title: str, people: str, notes: str) -> str:
    final_state = meeting_app.invoke(
        {
            "title": title,
            "people": people,
            "notes": notes,
            "error": "",
            "meeting_info": "",
            "summary": "",
            "actions": "",
            "result": ""
        }
    )
    return final_state["result"]

    