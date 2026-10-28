from statistics import mean


def build_summary(records: list[dict]) -> dict:
    if not records:
        return {
            "period": "데이터 없음",
            "count": 0,
            "metrics": {"total": 0, "average": 0, "max": 0, "min": 0},
            "trend": "판단할 데이터가 없습니다",
            "trend_rate": 0,
            "latest": None,
        }

    ordered = sorted(records, key=lambda row: str(row["date"]))
    values = [float(row["value"]) for row in ordered]
    window = max(1, min(14, len(values) // 3))
    recent_average = mean(values[-window:])
    previous_values = values[-window * 2 : -window]
    previous_average = mean(previous_values) if previous_values else recent_average
    rate = ((recent_average - previous_average) / previous_average * 100) if previous_average else 0
    direction = "상승" if rate > 3 else "하락" if rate < -3 else "유지"

    return {
        "period": f"{ordered[0]['date']} ~ {ordered[-1]['date']}",
        "count": len(values),
        "metrics": {
            "total": round(sum(values), 2),
            "average": round(mean(values), 2),
            "max": round(max(values), 2),
            "min": round(min(values), 2),
        },
        "trend": f"{direction} (최근 {window}개 평균 {rate:+.1f}%)",
        "trend_rate": round(rate, 1),
        "latest": {"date": str(ordered[-1]["date"]), "value": values[-1]},
    }

