# [DB관련 설정들 모아모아]
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent / "meetings.db"

# DB 연결
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# DB 초기화 함수
def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            create table if not exists meetings (
                id integer primary key autoincrement,
                title varchar(1000) not null,
                people varchar(1000) not null,
                notes text not null,
                summary text not null,
                actions text not null,
                result text not null,
                created_at varchar(100) not null
            )
            """
        )
        conn.commit()

# 회의 정보 저장 함수
def save_meeting(title: str, people: str, notes: str, summary: str, actions: str, result: str) -> int:
    # 현재 시각을 UTC 기준으로 생성(초까지 표현되도록 설정)
    created_at = datetime.now(timezone.utc).isoformat(timespec='seconds')

    with get_connection() as conn:
        cursor = conn.execute(
            """
            insert into meetings (title, people, notes, summary, actions, result, created_at)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, people, notes, summary, actions, result, created_at)
        )
        conn.commit()
        return int(cursor.lastrowid)