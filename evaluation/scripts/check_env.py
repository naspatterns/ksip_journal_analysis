"""환경 검증 — 새 컴퓨터에서 작업 시작 전 한 번 실행.

각 항목을 PASS/FAIL 로 출력. FAIL 시 화면 안내 따라 조치.

실행:
    .venv/bin/python evaluation/scripts/check_env.py
또는 그냥:
    python evaluation/scripts/check_env.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# verification/ 의 경로 helper 재사용
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verification"))


def _check(label: str, func, hint: str = "") -> bool:
    try:
        result = func()
        if result is True or (result and not isinstance(result, bool)):
            detail = f"  → {result}" if isinstance(result, (str, Path)) else ""
            print(f"  ✓ {label}{detail}")
            return True
        print(f"  ✗ {label}")
        if hint:
            print(f"    HINT: {hint}")
        return False
    except Exception as e:
        print(f"  ✗ {label}: {e}")
        if hint:
            print(f"    HINT: {hint}")
        return False


def main() -> int:
    print("\n=== 환경 검증 ===\n")
    all_ok = True

    # 1. Python 버전
    py_ok = sys.version_info >= (3, 10)
    print(f"  {'✓' if py_ok else '✗'} Python {sys.version.split()[0]}"
          f"  (>=3.10 필요)")
    all_ok &= py_ok

    # 2. venv 활성화
    in_venv = sys.prefix != sys.base_prefix
    print(f"  {'✓' if in_venv else '·'} venv: {sys.prefix}"
          f"  {'(활성화됨)' if in_venv else '(시스템 python 사용 중 — venv 권장)'}")

    # 3. 필수 패키지
    print("\n  의존 패키지:")
    required = ["pandas", "yaml", "ruamel.yaml", "requests", "pyarrow", "xlrd"]
    optional = ["openpyxl"]  # .xlsx 처리용, .xls 만 있는 현 데이터엔 불필요
    for pkg in required:
        try:
            __import__(pkg.split(".")[0])
            print(f"    ✓ {pkg}")
        except ImportError as e:
            print(f"    ✗ {pkg}  ({e})")
            all_ok = False
    for pkg in optional:
        try:
            __import__(pkg.split(".")[0])
            print(f"    ✓ {pkg}  (optional)")
        except ImportError:
            print(f"    · {pkg}  (optional, .xlsx 처리 시 필요)")

    # 4. 경로 자동 탐지
    print("\n  경로 자동 탐지:")
    try:
        from _common import (find_kci_key_file, find_main_root, find_raw_dir,
                             PROCESSED_DIR, DICT_DIR)
        main_root = find_main_root()
        print(f"    ✓ find_main_root: {main_root}")
    except Exception as e:
        print(f"    ✗ find_main_root: {e}")
        print(f"      HINT: KSIP_HOME 환경변수 설정 또는 디렉토리 이름 확인")
        all_ok = False
        main_root = None

    if main_root:
        # 5. processed parquet 4개
        for p in ["papers.parquet", "keywords.parquet",
                  "authors.parquet", "references.parquet"]:
            f = PROCESSED_DIR / p
            ok = f.exists()
            print(f"    {'✓' if ok else '✗'} data/processed/{p}"
                  f"  {'(' + str(f.stat().st_size // 1024) + ' KB)' if ok else ''}")
            all_ok &= ok

        # 6. dictionaries 4개
        for d in ["concepts.yml", "authors.yml", "journals.yml",
                  "institutions.yml"]:
            f = DICT_DIR / d
            ok = f.exists()
            print(f"    {'✓' if ok else '✗'} data/dictionaries/{d}")
            all_ok &= ok

        # 7. raw 데이터
        try:
            raw = find_raw_dir()
            xls_files = sorted(raw.glob("*.xls"))
            if len(xls_files) >= 3:
                print(f"    ✓ find_raw_dir: {raw}  ({len(xls_files)} .xls 파일)")
            else:
                print(f"    ✗ find_raw_dir: {raw}  ({len(xls_files)} .xls — 3개 필요)")
                print(f"      HINT: data/raw/ 에 인도철학_*.xls 3개 배치 (cloud sync)")
                all_ok = False
        except Exception as e:
            print(f"    ✗ find_raw_dir: {e}")
            all_ok = False

        # 8. KCI API key
        try:
            key_file = find_kci_key_file()
            if key_file:
                # 키 로드 시도
                sys.path.insert(0, str(main_root /
                                       ".claude" / "worktrees")) if (main_root / ".claude").exists() else None
                # 더 직접적: 로드 함수 import
                spec_path = Path(__file__).resolve().parent.parent / "verification" / "verify_09_kci_spotcheck.py"
                if spec_path.exists():
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("v09", spec_path)
                    v09 = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(v09)
                    key = v09.load_api_key()
                    if key and len(key) >= 6:
                        print(f"    ✓ KCI API key: {key_file.name}  "
                              f"(loaded, length {len(key)})")
                    else:
                        print(f"    ✗ KCI API key: 파일은 있는데 로드 실패 — 형식 확인")
                        all_ok = False
                else:
                    print(f"    · KCI API key 파일 있음: {key_file.name} "
                          f"(로드 검증 skip)")
            else:
                print(f"    · KCI API key 파일 없음 — L10 (KCI spot-check) 만 영향")
                print(f"      HINT: 메인 프로젝트 루트에 KCI_OpenAPI_Key.txt 배치")
        except Exception as e:
            print(f"    · KCI API key 검증 실패: {e}")

    # 9. git 상태 (선택)
    print("\n  git 상태:")
    try:
        import subprocess
        result = subprocess.run(["git", "status", "--porcelain"],
                                capture_output=True, text=True,
                                cwd=str(Path(__file__).resolve().parent.parent.parent))
        if result.returncode == 0:
            if result.stdout.strip():
                print(f"    · uncommitted 변경 있음 ({len(result.stdout.splitlines())} 파일)")
            else:
                print(f"    ✓ working tree clean")
        else:
            print(f"    · git 상태 조회 실패")
    except Exception:
        print(f"    · git 사용 불가")

    # 결과
    print()
    if all_ok:
        print("=== 모든 필수 항목 PASS — 작업 시작 가능 ===")
        print()
        print("다음 단계:")
        print("  cat evaluation/docs/SESSION_STATE.md  # 현재 위치 확인")
        return 0
    else:
        print("=== 일부 FAIL — 위 HINT 따라 조치 후 다시 실행 ===")
        return 1


if __name__ == "__main__":
    sys.exit(main())
