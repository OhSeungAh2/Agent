# 프로젝트 목적

학생의 이름과 점수를 등록하고, 등록된 학생 정보를 기반으로 다음 기능을 제공하는 콘솔 프로그램을 구현합니다.

- 전체 학생 목록 조회
- 전체 학생의 평균 점수 계산
- 최고 점수 학생 조회

# 필수 기능 목록

1. 학생 이름과 점수 등록
2. 등록된 전체 학생 목록 조회
3. 전체 학생 평균 점수 계산
4. 최고 점수 학생 조회
5. 프로그램 종료

# 입력과 출력

## 입력

- 메뉴 번호
- 학생 이름
- 학생 점수

## 출력

- 등록된 학생 목록
- 평균 점수
- 최고 점수 학생의 이름과 점수
- 입력 오류 또는 등록된 학생이 없을 때의 안내 메시지

# 예외 처리 요구사항

- 메뉴에 없는 번호를 입력하면 오류 메시지를 출력합니다.
- 점수에 숫자가 아닌 값을 입력하면 다시 입력하도록 안내합니다.
- 학생 목록이 비어 있을 때 평균 점수와 최고 점수를 조회하면 안내 메시지를 출력합니다.
- 학생 이름이 비어 있으면 등록하지 않습니다.
- 점수의 허용 범위는 별도로 지정되지 않았으므로, 입력된 숫자 값을 그대로 저장합니다.

## Python 구현 예시

```python
students = []


def register_student():
    name = input("학생 이름을 입력하세요: ").strip()

    if not name:
        print("학생 이름은 비어 있을 수 없습니다.")
        return

    try:
        score = float(input("점수를 입력하세요: "))
    except ValueError:
        print("점수는 숫자로 입력해야 합니다.")
        return

    students.append({
        "name": name,
        "score": score
    })

    print(f"{name} 학생이 등록되었습니다.")


def show_students():
    if not students:
        print("등록된 학생이 없습니다.")
        return

    print("\n전체 학생 목록")
    print("-" * 30)

    for index, student in enumerate(students, start=1):
        print(f"{index}. 이름: {student['name']}, 점수: {student['score']:.2f}")


def calculate_average():
    if not students:
        print("등록된 학생이 없어 평균을 계산할 수 없습니다.")
        return

    average = sum(student["score"] for student in students) / len(students)
    print(f"전체 학생 평균 점수: {average:.2f}")


def show_top_students():
    if not students:
        print("등록된 학생이 없어 최고 점수를 조회할 수 없습니다.")
        return

    highest_score = max(student["score"] for student in students)
    top_students = [
        student for student in students
        if student["score"] == highest_score
    ]

    print(f"\n최고 점수: {highest_score:.2f}")
    for student in top_students:
        print(f"최고 점수 학생: {student['name']}")


def main():
    while True:
        print("\n학생 성적 관리 프로그램")
        print("1. 학생 등록")
        print("2. 전체 학생 목록 조회")
        print("3. 평균 점수 계산")
        print("4. 최고 점수 학생 조회")
        print("5. 종료")

        choice = input("메뉴를 선택하세요: ").strip()

        if choice == "1":
            register_student()
        elif choice == "2":
            show_students()
        elif choice == "3":
            calculate_average()
        elif choice == "4":
            show_top_students()
        elif choice == "5":
            print("프로그램을 종료합니다.")
            break
        else:
            print("올바른 메뉴 번호를 입력하세요.")


if __name__ == "__main__":
    main()
```

이 구현은 동일한 이름의 학생도 별도의 등록 항목으로 저장하며, 최고 점수가 같은 학생이 여러 명이면 모두 출력합니다.