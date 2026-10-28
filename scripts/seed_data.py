import math
import random
from datetime import date, timedelta

from backend.dependencies import get_repository


def main() -> None:
    repo = get_repository()
    if repo.list_data():
        print("데이터가 이미 있어 시드를 건너뜁니다.")
        return

    random.seed(42)
    start = date(2026, 7, 1)
    for index in range(120):
        current = start + timedelta(days=index)
        baseline = 120 + index * 0.42
        weekly = 12 * math.sin(index * math.pi / 3.5)
        value = round(max(0, baseline + weekly + random.uniform(-5, 5)), 1)
        repo.create_data({"date": current.isoformat(), "value": value, "memo": "일일 학습 시간(분)"})
    print("120개 샘플 데이터를 저장했습니다.")


if __name__ == "__main__":
    main()
