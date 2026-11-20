# 프로젝트 목적

학생 이름과 점수를 함수 호출을 통해 등록하고, 등록된 학생 정보를 바탕으로 다음 기능을 제공하는 함수형 API를 설계합니다.

- 학생 등록
- 전체 학생 목록 조회
- 평균 점수 계산
- 최고 점수 학생 조회
- 동일한 최고 점수 학생 여러 명 처리
- 입력 대기나 콘솔 입출력 없이 호출 결과 반환

Python 표준 라이브러리만 사용하며, 전역 상태를 사용하지 않고 함수의 반환값으로 새로운 학생 목록을 생성합니다.

# 필수 기능 목록

1. 학생 이름과 점수 등록
2. 전체 학생 목록 조회
3. 전체 학생 평균 점수 계산
4. 최고 점수 학생 조회
5. 최고 점수가 같은 학생 모두 조회
6. 빈 학생 목록에 대한 예외 처리
7. 잘못된 이름과 점수에 대한 검증
8. 입력 대기 없는 함수형 API 제공

# 자료구조

## 학생 자료구조

학생 한 명은 `Student` 불변 데이터 클래스로 관리합니다.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Student:
    name: str
    score: float
```

- `name`: 학생 이름
- `score`: 학생 점수
- `frozen=True`: 등록된 학생 정보를 임의로 변경하지 못하도록 설정

## 학생 목록 자료구조

학생 목록은 불변 튜플을 사용합니다.

```python
StudentRecords = tuple[Student, ...]
```

튜플을 사용하는 이유는 다음과 같습니다.

- 전역 변수 없이 상태 관리 가능
- 함수가 기존 목록을 직접 변경하지 않음
- 등록 함수가 새로운 목록을 반환함
- 함수형 프로그래밍 방식에 적합함

# 함수 목록과 함수별 역할

| 함수 | 시그니처 | 역할 |
|---|---|---|
| `create_records` | `create_records() -> StudentRecords` | 빈 학생 목록 생성 |
| `register_student` | `register_student(records: StudentRecords, name: str, score: float \| int \| str) -> StudentRecords` | 학생을 등록하고 새로운 목록 반환 |
| `list_students` | `list_students(records: StudentRecords) -> StudentRecords` | 전체 학생 목록 반환 |
| `calculate_average` | `calculate_average(records: StudentRecords) -> float` | 전체 학생 평균 점수 계산 |
| `find_top_students` | `find_top_students(records: StudentRecords) -> tuple[Student, ...]` | 최고 점수 학생 모두 반환 |
| `_normalize_name` | `_normalize_name(name: str) -> str` | 학생 이름 검증 및 공백 제거 |
| `_normalize_score` | `_normalize_score(score: float \| int \| str) -> float` | 점수 검증 및 `float` 변환 |

# 프로그램 흐름

1. `create_records()`를 호출하여 빈 학생 목록을 생성합니다.
2. `register_student()`에 현재 목록, 이름, 점수를 전달합니다.
3. 함수는 기존 목록을 변경하지 않고 학생이 추가된 새 튜플을 반환합니다.
4. 반환된 새 목록을 다음 함수 호출에 사용합니다.
5. `list_students()`로 전체 학생을 조회합니다.
6. `calculate_average()`로 평균 점수를 계산합니다.
7. `find_top_students()`로 최고 점수 학생을 조회합니다.
8. 학생 목록이 비어 있는 경우 `EmptyStudentRecordsError`를 처리합니다.

## 함수형 사용 예시

```python
records = create_records()

records = register_student(records, "김민수", 85)
records = register_student(records, "이서연", "92.5")
records = register_student(records, "박지훈", 92.5)

students = list_students(records)
average = calculate_average(records)
top_students = find_top_students(records)
```

# 구현 코드

```python
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import TypeAlias


@dataclass(frozen=True)
class Student:
    """학생 한 명의 이름과 점수를 표현합니다."""

    name: str
    score: float


StudentRecords: TypeAlias = tuple[Student, ...]


class EmptyStudentRecordsError(LookupError):
    """학생 목록이 비어 있을 때 발생하는 예외입니다."""


def create_records() -> StudentRecords:
    """
    빈 학생 목록을 생성합니다.

    Returns:
        StudentRecords: 빈 학생 튜플
    """
    return ()


def _normalize_name(name: str) -> str:
    """
    학생 이름을 검증하고 앞뒤 공백을 제거합니다.

    Args:
        name: 학생 이름

    Returns:
        str: 정리된 학생 이름

    Raises:
        TypeError: 이름이 문자열이 아닌 경우
        ValueError: 이름이 비어 있는 경우
    """
    if not isinstance(name, str):
        raise TypeError("학생 이름은 문자열이어야 합니다.")

    normalized_name = name.strip()

    if not normalized_name:
        raise ValueError("학생 이름은 비어 있을 수 없습니다.")

    return normalized_name


def _normalize_score(score: float | int | str) -> float:
    """
    점수를 실수로 변환하고 유효성을 검증합니다.

    숫자로 변환 가능한 문자열도 허용합니다.
    점수의 최소·최대 범위는 제한하지 않습니다.

    Args:
        score: 숫자 또는 숫자로 변환 가능한 문자열

    Returns:
        float: 실수로 변환된 점수

    Raises:
        TypeError: 점수가 지원되지 않는 자료형인 경우
        ValueError: 점수가 숫자로 변환되지 않거나 유한하지 않은 경우
    """
    if isinstance(score, bool):
        raise TypeError("점수는 bool이 아닌 숫자여야 합니다.")

    if not isinstance(score, (int, float, str)):
        raise TypeError("점수는 int, float 또는 숫자 문자열이어야 합니다.")

    try:
        normalized_score = float(score)
    except ValueError as error:
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
    학생을 등록하고 새 학생 목록을 반환합니다.

    기존 records 튜플은 변경되지 않습니다.
    동일한 이름의 학생도 별도 학생으로 등록됩니다.

    Args:
        records: 기존 학생 목록
        name: 등록할 학생 이름
        score: 등록할 학생 점수

    Returns:
        StudentRecords: 학생이 추가된 새로운 학생 목록

    Raises:
        TypeError: records, name 또는 score의 자료형이 잘못된 경우
        ValueError: 이름 또는 점수가 유효하지 않은 경우
    """
    if not isinstance(records, tuple):
        raise TypeError("학생 목록은 tuple이어야 합니다.")

    normalized_name = _normalize_name(name)
    normalized_score = _normalize_score(score)

    student = Student(
        name=normalized_name,
        score=normalized_score,
    )

    return records + (student,)


def list_students(records: StudentRecords) -> StudentRecords:
    """
    전체 학생 목록을 반환합니다.

    Args:
        records: 학생 목록

    Returns:
        StudentRecords: 전체 학생 목록

    Raises:
        TypeError: records가 tuple이 아닌 경우
    """
    if not isinstance(records, tuple):
        raise TypeError("학생 목록은 tuple이어야 합니다.")

    return records


def calculate_average(records: StudentRecords) -> float:
    """
    전체 학생의 평균 점수를 계산합니다.

    Args:
        records: 학생 목록

    Returns:
        float: 평균 점수

    Raises:
        TypeError: records가 tuple이 아닌 경우
        EmptyStudentRecordsError: 학생 목록이 비어 있는 경우
    """
    if not isinstance(records, tuple):
        raise TypeError("학생 목록은 tuple이어야 합니다.")

    if not records:
        raise EmptyStudentRecordsError(
            "등록된 학생이 없어 평균을 계산할 수 없습니다."
        )

    return sum(student.score for student in records) / len(records)


def find_top_students(
    records: StudentRecords,
) -> tuple[Student, ...]:
    """
    최고 점수를 받은 학생을 모두 반환합니다.

    최고 점수가 같은 학생이 여러 명이면 등록 순서를 유지하여
    모두 반환합니다.

    Args:
        records: 학생 목록

    Returns:
        tuple[Student, ...]: 최고 점수 학생 목록

    Raises:
        TypeError: records가 tuple이 아닌 경우
        EmptyStudentRecordsError: 학생 목록이 비어 있는 경우
    """
    if not isinstance(records, tuple):
        raise TypeError("학생 목록은 tuple이어야 합니다.")

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
```

# 예외처리 요구사항

## 1. 빈 이름

학생 이름이 빈 문자열이거나 공백만 포함하면 `ValueError`를 발생시킵니다.

```python
register_student(records, "   ", 80)
```

발생 예외:

```python
ValueError: 학생 이름은 비어 있을 수 없습니다.
```

## 2. 숫자가 아닌 점수

점수가 숫자로 변환되지 않으면 `ValueError`를 발생시킵니다.

```python
register_student(records, "김민수", "점수없음")
```

발생 예외:

```python
ValueError: 점수는 숫자로 입력해야 합니다.
```

## 3. 비어 있는 학생 목록의 평균 계산

```python
calculate_average(records)
```

학생 목록이 비어 있으면 `EmptyStudentRecordsError`를 발생시킵니다.

## 4. 비어 있는 학생 목록의 최고 점수 조회

```python
find_top_students(records)
```

학생 목록이 비어 있으면 `EmptyStudentRecordsError`를 발생시킵니다.

## 5. 예외 처리 사용 예시

```python
records = create_records()

try:
    average = calculate_average(records)
except EmptyStudentRecordsError as error:
    print(error)

try:
    records = register_student(records, "", 90)
except ValueError as error:
    print(error)
```

이 설계에서는 함수 내부에서 `input()`이나 `print()`를 호출하지 않습니다. 따라서 웹 애플리케이션, GUI, 테스트 코드, CLI 등 다양한 호출 환경에서 동일한 함수를 재사용할 수 있습니다.