# Resource Index — 별도 폴더에서 본 폴더의 자원을 활용하는 가이드

> **언제 읽나**: 사용자가 본 폴더(`ksip_journal_analysis/`)의 분석 자원을
> 별도 폴더의 새 대시보드·앱·노트북에서 사용하려 할 때.
>
> **요약**: 본 폴더는 분석 데이터 + 사전 + 패키지의 *원천 저장소*. 새 폴더는
> 시각화·검수 UI·논문 작성 등 *소비자*. 데이터 경로를 환경변수로 노출하고
> ksip 패키지를 editable install 하면 두 폴더가 깔끔하게 분리됨.

---

## 1. 본 폴더가 제공하는 자원

### 1.1 분석 데이터 (`data/processed/`, git 포함, ~3MB)

| 파일 | 행 | 핵심 컬럼 (Phase 5R3 기준) |
|---|---:|---|
| `papers.parquet` | 636 | 논문 ID·논문명·저자명·주저자 소속기관·발행연도·초록·기관_부모 + 25개 메타 |
| `keywords.parquet` | 3,089 | 논문ID·발행연도·키워드_원본·canonical_id |
| `authors.parquet` | 654 | 저자_원본·canonical_id |
| `references.parquet` | 12,887 | 논문ID·참조번호·유형(7종)·저자_원본·제목_원본·학술지_원본·연도·DOI·URL·자기인용·원본_텍스트·학술지_canonical·**tier** (Phase 4.3 추가, primary/secondary/unknown) |
| `paper_labels.parquet` | 636 | 논문ID·**primary_source_basis**·**secondary_source_horizon**·**primary_basis_source** (refs / keywords_title / none)·n_primary·n_secondary·n_inferred·primary_dist·secondary_dist (Phase 4.4 + 5R3 산출물) |

**기타 산출물** (main 브랜치만 — claude 브랜치엔 없음):
- `kci_papers.parquet`, `kci_authors.parquet`, `kci_references.parquet`, `journal_metrics.parquet`, `journal_change_history.parquet` — KCI Open API 통합 결과 (Stage 2, main 브랜치)

### 1.2 Authority 사전 (`data/dictionaries/`, git 포함, ~50KB)

| 파일 | entry | 메타필드 |
|---|---:|---|
| `concepts.yml` | 96 | canonical_id·canonical_kr/iast/zh·type (학자/인물/원전/문헌/학파/개념)·school·era·**tradition_language** (Decision-18 후)·reception_horizon·century·surface_forms·verified·notes |
| `authors.yml` | 63 | canonical_id·canonical_form·affiliation·**horizon** (korean/japanese/english/german/french, Phase 5R1 추가)·surface_forms·verified |
| `journals.yml` | 53 | canonical_id·canonical_form·publisher·issn·surface_forms·verified |
| `institutions.yml` | (예외만) | canonical_id·canonical_form·surface_forms |

**원칙**: surface 절대 덮어쓰지 않음. `canonical_id` 만 추가.

### 1.3 Python 패키지 (`ksip/`, git 포함)

순수 Python, Streamlit 의존 없음. 새 폴더에서 그대로 reuse 가능.

| 모듈 | 핵심 함수 |
|---|---|
| `ksip.load` | `load_papers` / `explode_authors` / `explode_keywords` — 원본 .xls → long-form |
| `ksip.references` | `parse_one(raw)` / `load_references` — 7유형 슬래시 파서 |
| `ksip.normalize` | `add_canonical_column` / `load_authority` / `resolve_person` / `coverage_report` — Authority Control |
| `ksip.clean` | `clean_title` / `clean_keyword` — PUA·트레일링 underscore 제거 |
| `ksip.institutions` | `parent_institution` — 기관 부모 단위 (동국대학교 14변형 통합) |
| `ksip.citations` | `landscape_stats` + ego-network 집계 |
| `ksip.concepts` | `concept_timeseries` / `cooccurrence_topk` 등 — 개념 탐험기 집계 |
| `ksip.data` | `load_papers()` / `load_keywords()` / 등 — parquet loader (Streamlit 페이지가 사용) |

### 1.4 평가 라벨링 패키지 (`evaluation/labeling/`)

Phase 4-5 산출물. 새 대시보드가 라벨링 결과를 다시 계산하려면 이걸 import.

| 모듈 | 함수 |
|---|---|
| `evaluation.labeling.detect_language` | `build_concepts_primary_lookup` / `build_concepts_all_lookup` / `build_canonical_id_primary_lookup` / `build_authors_horizon_lookup` / `build_journals_horizon_lookups` / `detect_primary_language` / `detect_primary_from_text` / `detect_secondary_horizon` |
| `evaluation.labeling.classify_reference_tier` | tier 분류 (primary/secondary/unknown) |
| `evaluation.labeling.compute_paper_source` | paper-level 두 변수 집계 (refs + keywords/title fallback) |

### 1.5 검수 입력 (`evaluation/output/`)

- `review_sample.csv` — Phase 5 검수 표본 100 paper (random 50 + low-confidence 50, UTF-8 BOM, 16 컬럼)

---

## 2. 새 폴더에서의 권장 셋업

### 2.1 권장 폴더 구조 (예: 새 대시보드 이름 `<NEW_NAME>`)

```
<NEW_NAME>/
├── README.md
├── CLAUDE.md                     # 이 폴더의 캐논 (어디서 데이터를 가져오는지 명시)
├── .gitignore
├── requirements.txt              # 새 의존성
├── pyproject.toml 또는 setup.cfg # ksip + evaluation.labeling 을 editable 로 설치
├── .venv/                        # 별도 venv
├── app.py                        # Streamlit 진입점 (또는 다른 프레임워크)
├── pages/                        # Streamlit 멀티페이지
├── src/<new_pkg>/                # 새 패키지 (재사용 가능 로직)
├── data/                         # ★ 이 폴더는 데이터를 직접 보유하지 않음 — env 로 외부 참조
│   └── (없음 or symlink or cache)
├── notebooks/                    # 실험 노트북
└── tests/
```

### 2.2 데이터 접근 패턴 — 환경변수 (★ 권장)

본 폴더의 절대 경로를 환경변수로 지정. 새 코드는 이 env 를 읽음. cloud sync·multi-machine 환경에서 가장 안전.

```bash
# .envrc 또는 ~/.zshrc 에 export
export KSIP_HOME="/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/다른 컴퓨터/내 Mac/Documents/@CLASSES/2026-1/DigitalHumanities/ksip_journal_analysis"
```

새 코드 (예시):

```python
# src/<new_pkg>/paths.py
import os
from pathlib import Path

KSIP_HOME = Path(os.environ.get("KSIP_HOME", "")).resolve()
if not KSIP_HOME.exists():
    raise RuntimeError(
        "KSIP_HOME 환경변수가 미설정. ksip_journal_analysis 폴더의 절대 경로를 지정하세요.\n"
        "예: export KSIP_HOME='/Users/jibak/.../ksip_journal_analysis'"
    )

DATA_DIR = KSIP_HOME / "data" / "processed"
DICT_DIR = KSIP_HOME / "data" / "dictionaries"

def load_paper_labels():
    import pandas as pd
    return pd.read_parquet(DATA_DIR / "paper_labels.parquet")

def load_papers():
    import pandas as pd
    return pd.read_parquet(DATA_DIR / "papers.parquet")
```

**대안**: `direnv` 로 폴더 진입 시 자동 export, 또는 `python-dotenv` 로 `.env` 파일 읽기.

### 2.3 ksip 패키지 import — editable install (★ 권장)

본 폴더의 `ksip/` 와 `evaluation/labeling/` 를 새 폴더에서 import 하려면:

```bash
# 새 폴더의 venv 활성화 후
pip install -e "$KSIP_HOME"
```

본 폴더에 `pyproject.toml` 또는 `setup.py` 가 있어야 함. **현재 본 폴더엔 없음**. 새 작업 시작 전에 본 폴더에 다음을 추가하는 것이 깔끔:

```toml
# ksip_journal_analysis/pyproject.toml (옵션 — 추가 권장)
[project]
name = "ksip_journal_analysis"
version = "0.1.0"
requires-python = ">=3.10"

[tool.setuptools]
packages = ["ksip", "evaluation.labeling"]
```

또는 `pyproject.toml` 추가가 번거롭다면:

**옵션 (b) — sys.path 조작** (단순하지만 IDE 지원·테스트 분리에 불리):
```python
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(os.environ["KSIP_HOME"]).resolve()))
from ksip.data import load_papers
from evaluation.labeling.detect_language import detect_primary_language
```

**옵션 (c) — symlink** (cloud sync 환경에서 깨질 위험):
```bash
ln -s "$KSIP_HOME/ksip" ./src/ksip
ln -s "$KSIP_HOME/evaluation" ./src/evaluation
```

### 2.4 venv 와 의존성 분리

새 폴더는 자체 venv 를 둠. 본 폴더의 `.venv/` 와 공유하지 마세요 (의존성 충돌·버전 lock 가시성 저하).

새 폴더의 `requirements.txt` 최소:
```
pandas
pyarrow
pyyaml
ruamel.yaml      # (사전 수정 필요 시)
streamlit        # (대시보드)
plotly           # (시각화)
```

본 폴더가 sys.path 또는 editable install 로 들어오면 본 폴더의 패키지 자체 의존성도 새 venv 에 설치 필요.

### 2.5 Git 전략

- **별도 repo 권장** — 새 작업의 독립성·history 보존
- 또는 monorepo 식: 본 폴더 안에 `dashboards/<NEW_NAME>/` 같은 서브디렉토리 (기존 `evaluation/` 패턴 따라)

새 별도 repo 생성:
```bash
cd /path/to/parent
mkdir <NEW_NAME>
cd <NEW_NAME>
git init
gh repo create naspatterns/<NEW_NAME> --private --source=. --remote=origin
```

본 폴더는 그대로 두고, 새 폴더는 이 자원의 *소비자* 로만 기능.

---

## 3. 새 폴더 셋업 체크리스트

- [ ] 새 폴더 위치 결정 (본 폴더와 같은 부모 디렉토리 권장 — Google Drive 동기화 일관성)
- [ ] `KSIP_HOME` 환경변수 설정 (셸 rc 또는 direnv)
- [ ] 새 폴더에 `.venv/` 생성, `pip install` 기본 의존성
- [ ] 본 폴더 `ksip/` 와 `evaluation/labeling/` 접근 방식 선택 (editable install / sys.path / symlink)
- [ ] 새 폴더 `CLAUDE.md` 첫 문장에 본 폴더의 위치·환경변수·사용하는 파일 명시
- [ ] 새 폴더 `.gitignore` 에 venv·cache·data/raw·`.streamlit/secrets.toml` 등 추가
- [ ] 첫 데이터 로딩 코드 (`load_paper_labels`) 가 동작하는지 셋업 검증
- [ ] git init + 원격 push 후 새 작업 시작

---

## 4. 본 폴더의 현재 상태 (Phase 5R3 직후)

- **브랜치**: `claude/festive-elgamal-1dd4b3` (origin 에 push, main 머지 X — 별도 트랙)
- **paper_labels.parquet 최신 상태** (Phase 5R3 후 636 paper):
  - primary_source_basis: sanskrit 387 / unknown 114 / chinese_canon 66 / pali 29 / mixed 24 / prakrit 11 / tibetan_canon 5
  - secondary_source_horizon: english 262 / unknown 155 / korean 113 / mixed 54 / japanese 52
- **검수 표본**: `evaluation/output/review_sample.csv` (100 paper) — 사용자 보류 상태
- **알려진 한계**: 단행본 secondary english 비중 61% (Indian Indology 매체), 일본 학자의 한국어 번역서 → korean 오분류, multi-slash 오류 30건 (main 만 fix)

본 폴더의 진행 상황 상세는 [`SESSION_STATE.md`](./SESSION_STATE.md), [`DECISIONS.md`](./DECISIONS.md), [`ISSUES.md`](./ISSUES.md), [`PIPELINE.md`](./PIPELINE.md) 참조.

---

## 5. 새 폴더에서 자주 쓸 코드 스니펫

### 5.1 paper × 라벨 join (대시보드의 기본 데이터)

```python
import pandas as pd
from pathlib import Path
import os

KSIP_HOME = Path(os.environ["KSIP_HOME"])
DATA = KSIP_HOME / "data" / "processed"

papers = pd.read_parquet(DATA / "papers.parquet").rename(columns={"논문 ID": "논문ID"})
labels = pd.read_parquet(DATA / "paper_labels.parquet")

paper_view = papers.merge(labels, on="논문ID", how="left")
# paper_view 컬럼: 논문ID·논문명·저자명·발행연도·... + primary_source_basis·secondary_source_horizon·primary_basis_source·...
```

### 5.2 6축 메타필드 lookup (concept-level)

```python
import yaml
from pathlib import Path
import os

DICT = Path(os.environ["KSIP_HOME"]) / "data" / "dictionaries"
concepts = yaml.safe_load((DICT / "concepts.yml").read_text(encoding="utf-8"))

# canonical_id → 6축 메타
meta = {
    e["canonical_id"]: {
        "school": e.get("school"),
        "era": e.get("era"),
        "tradition_language": e.get("tradition_language"),
        "reception_horizon": e.get("reception_horizon"),
    }
    for e in concepts if e.get("verified")
}
```

### 5.3 keywords × paper × concept meta join (커버리지 분석용)

```python
import pandas as pd
from pathlib import Path
import os

DATA = Path(os.environ["KSIP_HOME"]) / "data" / "processed"

kw = pd.read_parquet(DATA / "keywords.parquet")
# kw: 논문ID·발행연도·키워드_원본·canonical_id

# 6축 메타 join — kw 의 canonical_id → concepts 의 메타
import yaml
concepts = yaml.safe_load((DATA.parent / "dictionaries" / "concepts.yml").read_text(encoding="utf-8"))
meta_df = pd.DataFrame([
    {
        "canonical_id": e["canonical_id"],
        "school": e.get("school"),
        "era": e.get("era"),
        "tradition_language": e.get("tradition_language"),
        "reception_horizon": e.get("reception_horizon"),
    }
    for e in concepts if e.get("verified")
])

kw_with_meta = kw.merge(meta_df, on="canonical_id", how="left")
# kw_with_meta: 매칭된 키워드 + 6축 메타
```

### 5.4 cross-tab 의존도 패턴

```python
import pandas as pd
labels = pd.read_parquet(DATA / "paper_labels.parquet")
ct = pd.crosstab(
    labels["primary_source_basis"],
    labels["secondary_source_horizon"],
    margins=True, margins_name="합계",
)
print(ct)
# 인도철학회의 학적 의존도 패턴 — Phase 6 시각화의 핵심 입력
```

---

## 6. 본 폴더 손대지 말 것 / 주의사항

- **`data/raw/*.xls`** (gitignored) — 원본. 절대 수정 금지.
- **`data/processed/*.parquet`** — Phase 5R3 시점 산출물. 새 폴더가 수정하면 본 폴더의 작업과 충돌. 새 폴더는 **읽기 전용**으로만 접근.
- **`data/dictionaries/*.yml`** — 본 폴더의 분석에 사용. 새 폴더에서 수정해야 한다면 본 폴더에 PR.
- **`.venv/`** — 본 폴더의 venv. 새 폴더는 별도 venv 사용.
- **`evaluation/output/`** — 본 폴더의 검수·검증 산출물. 새 폴더가 같은 출력을 두려면 자체 디렉토리.

---

## 7. 갱신 이력

- 2026-05-20 — RESOURCE_INDEX.md 초안 작성 (사용자가 새 폴더에서 새 대시보드 작업 시작 시점)
