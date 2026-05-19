# 환경 설정 (Per Computer)

> 멀티 컴퓨터 작업. 새 컴퓨터에서 작업 시작 전에 이 절차를 한 번 수행.
> 작동 중인 컴퓨터에서는 [`SESSION_STATE.md`](./SESSION_STATE.md) 만 보면 됨.

---

## 1. 필요한 것

| 항목 | 설치 / 동기화 방법 |
|---|---|
| Python 3.14+ | https://python.org 또는 brew/conda |
| git | OS 패키지 매니저 |
| 메인 저장소 | `git clone https://github.com/naspatterns/ksip_journal_analysis.git` |
| 원본 데이터 (`data/raw/*.xls`) | **별도 sync** (Drive/Dropbox/scp) — gitignored |
| KCI Open API Key 파일 | **별도 sync** (gitignored) |

---

## 2. 초기 셋업 (저장소 받은 직후 1회)

### 2-1. 저장소 clone

```bash
git clone https://github.com/naspatterns/ksip_journal_analysis.git
cd ksip_journal_analysis
```

### 2-2. venv 생성 + 의존성 설치

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install ruamel.yaml requests pandas pyarrow openpyxl xlrd
```

(requirements.txt 만으로 부족하면 위 추가 패키지 명시 설치.)

### 2-3. raw 데이터 배치

`data/raw/` 에 다음 4개 파일 배치:

```
data/raw/
├── 인도철학_1_300.xls       (~3.5 MB)
├── 인도철학_301_600.xls     (~2.6 MB)
├── 인도철학_601_636.xls     (~40 KB)
└── 인도철학_통합.csv         (~2 MB)
```

→ 이전 컴퓨터에서 cloud sync 또는 직접 복사.

### 2-4. KCI API Key 배치

저장소 루트(`ksip_journal_analysis/`) 에 다음 형식 중 하나로 저장:

```bash
# 옵션 A — 파일로 (자동 탐지됨)
echo "KCI OpenAPI Key: 12345678" > "KCI_OpenAPI_Key 2.txt"
# 또는 두 줄 형식도 가능: "KCI OpenAPI Key\n\n12345678"

# 옵션 B — 환경변수
export KSIP_KCI_API_KEY="12345678"  # ~/.zshrc 등에 영구 저장
```

### 2-5. 환경 검증

```bash
.venv/bin/python evaluation/scripts/check_env.py
```

모든 체크 PASS 면 작업 시작 가능. 실패하면 화면 안내대로 조치.

---

## 3. 환경변수 (옵션)

자동 탐지가 안 되는 경우 명시적으로 지정:

```bash
# 저장소 위치 (기본: 디렉토리 이름이 ksip_journal_analysis 면 자동 탐지)
export KSIP_HOME="/path/to/ksip_journal_analysis"

# raw 데이터 위치 (기본: $KSIP_HOME/data/raw)
export KSIP_RAW_DIR="/path/to/raw"

# KCI 키 파일 (기본: $KSIP_HOME/KCI_OpenAPI_Key*.txt 자동 탐지)
export KSIP_KCI_KEY_FILE="/path/to/key.txt"

# KCI 키 값 자체 (위보다 우선)
export KSIP_KCI_API_KEY="12345678"
```

---

## 4. 워크트리 vs 메인 프로젝트

Claude Code 가 worktree (`<main>/.claude/worktrees/<temp>/`) 안에서 작업해도, 자동 탐지가 메인 프로젝트의 raw/key 를 찾음. 사용자가 별도 셋업할 필요 없음.

단, **워크트리에서 한 변경은 별도 브랜치 (`claude/...`) 에 커밋됨**. main 에 반영하려면 [`HANDOFF_PROTOCOL.md`](./HANDOFF_PROTOCOL.md) 의 "워크트리 → main 머지" 절차 참조.

---

## 5. 동기화 권장 도구

| 항목 | 도구 |
|---|---|
| 소스 코드 + parquet + dictionaries | git push/pull (origin 사용) |
| raw .xls 데이터 | iCloud Drive / Google Drive / Dropbox 의 동기 폴더 (저장소 *밖*) + symlink 또는 cp |
| KCI API key | 위와 동일 (보안 주의 — 공개 cloud 보다는 1Password 등이 안전) |

→ git 으로 못 추적하는 raw/key 만 별도 동기화. 나머지는 git 으로 다 됨.

---

## 6. 환경 점검 항목 (check_env.py 가 자동 검사)

- ☐ Python ≥ 3.10
- ☐ venv 활성화 (`.venv/bin/python` 존재)
- ☐ pandas / ruamel.yaml / requests / pyarrow / openpyxl import 성공
- ☐ `find_main_root()` 성공
- ☐ `data/processed/*.parquet` 4개 존재
- ☐ `data/dictionaries/*.yml` 4개 존재
- ☐ `find_raw_dir()` 존재 + .xls 3개 발견
- ☐ `find_kci_key_file()` 존재 + 키 로드 성공 (8자리 또는 그 이상의 영숫자)
- ☐ git working tree clean (옵션, warning)
