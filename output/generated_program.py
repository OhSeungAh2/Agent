from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import TypeAlias


@dataclass(frozen=True)
class Student:
    """학생 한 명의 이름과 점수를 나타냅니다."""

    name: str
    score: float


StudentRecords: TypeAlias = tuple[Student, ...]


class EmptyStudentRecordsError(LookupError):
    """학생 목록이 비어 있을 때 발생하는 예외입니다."""


def create_records() -> StudentRecords:
    """빈 학생 목록을 생성합니다."""
    return ()


def _validate_records(records: StudentRecords) -> None:
    """학생 목록의 자료형과 구성 요소를 검증합니다."""
    if not isinstance(records, tuple):
        raise TypeError("학생 목록은 tuple이어야 합니다.")

    if any(not isinstance(student, Student) for student in records):
        raise TypeError("학생 목록에는 Student 객체만 포함할 수 있습니다.")


def _normalize_name(name: str) -> str:
    """학생 이름을 검증하고 앞뒤 공백을 제거합니다."""
    if not isinstance(name, str):
        raise TypeError("학생 이름은 문자열이어야 합니다.")

    normalized_name = name.strip()

    if not normalized_name:
        raise ValueError("학생 이름은 비어 있을 수 없습니다.")

    return normalized_name


def _normalize_score(score: float | int | str) -> float:
    """
    점수를 유한한 실수로 변환합니다.

    점수의 최소값과 최대값은 제한하지 않습니다.
    """
    if isinstance(score, bool):
        raise TypeError("점수는 bool이 아닌 숫자여야 합니다.")

    if not isinstance(score, (int, float, str)):
        raise TypeError("점수는 int, float 또는 숫자 문자열이어야 합니다.")

    try:
        normalized_score = float(score)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("점수는 숫자로 입력해야 합니다.") from error

    if not isfinite(normalized_score):
        raise ValueError("점수는 유한한 숫자여야 합니다.")

    return normalized_score


def register_student(
    records: StudentRecords,
    name: str,
    score: float | int | str,
) -> StudentRecords:
    """
    학생을 등록하고 새로운 학생 목록을 반환합니다.

    기존 학생 목록은 변경하지 않습니다.
    동일한 이름의 학생도 별도의 등록 항목으로 저장합니다.
    """
    _validate_records(records)

    student = Student(
        name=_normalize_name(name),
        score=_normalize_score(score),
    )

    return records + (student,)


def list_students(records: StudentRecords) -> StudentRecords:
    """전체 학생 목록을 등록 순서대로 반환합니다."""
    _validate_records(records)
    return records


def calculate_average(records: StudentRecords) -> float:
    """전체 학생의 평균 점수를 계산합니다."""
    _validate_records(records)

    if not records:
        raise EmptyStudentRecordsError(
            "등록된 학생이 없어 평균을 계산할 수 없습니다."
        )

    return sum(student.score for student in records) / len(records)


def find_top_students(records: StudentRecords) -> tuple[Student, ...]:
    """
    최고 점수 학생을 모두 반환합니다.

    최고 점수가 같은 학생은 등록 순서를 유지하여 모두 반환합니다.
    """
    _validate_records(records)

    if not records:
        raise EmptyStudentRecordsError(
            "등록된 학생이 없어 최고 점수를 조회할 수 없습니다."
        )

    highest_score = max(student.score for student in records)

    return tuple(
        student
        for student in records
        if student.score == highest_score
    )