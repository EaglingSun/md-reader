"""sample.py — AI_docs reader 코드 보기 확인용 (읽기 전용 · 줄 번호).

이 파일은 실행하지 않는다. 앱에서 열어 색 · 줄 번호 · 편집 잠금을 확인한다.
"""
from pathlib import Path


def score(case_dir: Path) -> dict:
    """채점 규칙 예시 — 정답 줄 번호와 리뷰가 짚은 줄 번호를 비교한다."""
    expected = int((case_dir / "expected_line.txt").read_text(encoding="utf-8"))
    found = [int(x) for x in (case_dir / "found_lines.txt").read_text(encoding="utf-8").split()]
    # TODO: 줄 번호가 ±1 이내면 맞은 것으로 볼지 정한다
    hit = expected in found
    return {"case": case_dir.name, "expected": expected, "found": found, "hit": hit}


if __name__ == "__main__":
    for d in sorted(Path("cases").glob("E0*")):
        print(score(d))
