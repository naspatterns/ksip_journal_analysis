"""concepts.yml 의 69개 entry 에 분류 체계 메타필드 backfill.

추가 필드 (SCHEMA.md 기준):
- school              : primary_school 라벨 (yoga/yogacara/madhyamaka 등)
- era                 : 분류 시대 (classical/post_classical 등)
- source_language     : 1차 자료 언어 (sanskrit/pali/chinese/tibetan 등)
- reception_horizon   : 지평 (india/east_asia/tibet/korea/west)

기존 free-form `era: 7세기` 같은 필드는 `century:` 로 rename (충돌 회피).
ruamel.yaml 사용 — 주석/섹션 구분 보존.

실행:
    .venv/bin/python evaluation/labeling/backfill_concepts_metadata.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parent.parent.parent
CONCEPTS_PATH = ROOT / "data" / "dictionaries" / "concepts.yml"


# ============================================================
# 메타데이터 매핑 — canonical_id → (school, era, source_language, reception_horizon)
# 보수적으로: 다중 학파 후보 시 가장 대표적인 1개. 검수 단계에서 보강 가능.
# ============================================================

# `transversal` = 시대 가로지름, `n/a` = 해당없음
METADATA: dict[str, tuple[str, str, str, str]] = {
    # ── 학자 (인도) ────────────────────────────────────────
    "dharmakirti":     ("pramana",     "post_classical",    "sanskrit", "india"),
    "dignaga":         ("pramana",     "classical",         "sanskrit", "india"),
    "nagarjuna":       ("madhyamaka",  "classical",         "sanskrit", "india"),
    "vasubandhu":      ("yogacara",    "classical",         "sanskrit", "india"),
    "asanga":          ("yogacara",    "classical",         "sanskrit", "india"),
    "shankara":        ("vedanta",     "post_classical",    "sanskrit", "india"),
    "patanjali":       ("yoga",        "classical",         "sanskrit", "india"),
    "buddhaghosa":     ("abhidharma",  "classical",         "pali",     "india"),
    "candrakirti":     ("madhyamaka",  "post_classical",    "sanskrit", "india"),
    "bhavaviveka":     ("madhyamaka",  "classical",         "sanskrit", "india"),
    "shantarakshita":  ("madhyamaka",  "post_classical",    "sanskrit", "india"),

    # ── 학자 보강 (동아시아/한국/근대) ───────────────────
    # 玄奘: 한역가지만 그 학적 작업은 인도 유식 — reception=india 로 둠
    "xuanzang":        ("yogacara",    "classical",         "chinese",  "india"),
    # 원효: 한국 불교 — reception=korea
    "wonhyo":          ("korean_buddhism", "classical",     "chinese",  "korea"),
    # 간디: 근대 인도
    "gandhi":          ("hindu_modern","modern",            "mixed",    "india"),

    # ── 학파 ────────────────────────────────────────────
    "yogacara":        ("yogacara",    "classical",         "sanskrit", "india"),
    "madhyamaka":      ("madhyamaka",  "classical",         "sanskrit", "india"),
    "sautrantika":     ("abhidharma",  "classical",         "sanskrit", "india"),
    "vaibhashika":     ("abhidharma",  "classical",         "sanskrit", "india"),
    "samkhya":         ("samkhya",     "classical",         "sanskrit", "india"),
    "vaisheshika":     ("vaisheshika", "classical",         "sanskrit", "india"),
    "nyaya":           ("nyaya",       "classical",         "sanskrit", "india"),
    "vedanta":         ("vedanta",     "classical",         "sanskrit", "india"),
    # 아드와이타: vedanta 하위지만 단일 라벨 정책이므로 school=vedanta
    "advaita_vedanta": ("vedanta",     "post_classical",    "sanskrit", "india"),
    "jainism":         ("jainism",     "classical",         "prakrit",  "india"),
    "tantric_buddhism":("tantric_buddhism", "post_classical","sanskrit","india"),

    # ── 핵심 개념 ───────────────────────────────────────
    "shunyata":        ("madhyamaka",  "classical",         "sanskrit", "india"),
    "pramana":         ("pramana",     "classical",         "sanskrit", "india"),
    "svasamvedana":    ("pramana",     "post_classical",    "sanskrit", "india"),
    "trisvabhava":     ("yogacara",    "classical",         "sanskrit", "india"),
    "tathagatagarbha": ("yogacara",    "classical",         "sanskrit", "india"),
    "alaya_vijnana":   ("yogacara",    "classical",         "sanskrit", "india"),
    # 연기·무아: 초기불교 — 시대로는 우파니샤드-수트라 시기. 학파는 광범위 → madhyamaka 로 기본
    "pratityasamutpada":("madhyamaka", "upanishadic_sutra", "sanskrit", "india"),
    "anatman":         ("madhyamaka",  "upanishadic_sutra", "sanskrit", "india"),
    # 아트만: 우파니샤드 핵심
    "atman":           ("vedanta",     "upanishadic_sutra", "sanskrit", "india"),
    # 업·해탈·윤회: 학파 가로지름. school 은 가장 대표성 있는 것으로 (학파 라벨은 임시; 검수 환류)
    "karma":           ("vedanta",     "transversal",       "sanskrit", "india"),
    "moksha":          ("vedanta",     "transversal",       "sanskrit", "india"),
    "samsara":         ("vedanta",     "transversal",       "sanskrit", "india"),
    # 요가 (개념): 학파 가로지름
    "yoga":            ("yoga",        "transversal",       "sanskrit", "india"),
    "prajna":          ("madhyamaka",  "classical",         "sanskrit", "india"),
    "catuskoti":       ("madhyamaka",  "classical",         "sanskrit", "india"),
    "vijnanavada":     ("yogacara",    "classical",         "sanskrit", "india"),
    "apoha":           ("pramana",     "post_classical",    "sanskrit", "india"),
    "vipasyana":       ("abhidharma",  "upanishadic_sutra", "pali",     "india"),
    "svabhava":        ("madhyamaka",  "classical",         "sanskrit", "india"),
    "smrti":           ("abhidharma",  "upanishadic_sutra", "pali",     "india"),
    "vijnana_parinama":("yogacara",    "classical",         "sanskrit", "india"),
    "tathata":         ("yogacara",    "classical",         "sanskrit", "india"),
    "paramartha_satya":("madhyamaka",  "classical",         "sanskrit", "india"),
    "dvi_satya":       ("madhyamaka",  "classical",         "sanskrit", "india"),
    "purusa":          ("samkhya",     "classical",         "sanskrit", "india"),
    "meditation":      ("comparative", "transversal",       "n/a",      "india"),
    "alamkara":        ("comparative", "post_classical",    "sanskrit", "india"),
    "abhuta_parikalpa":("yogacara",    "classical",         "sanskrit", "india"),
    "sanskrit_lang":   ("comparative", "transversal",       "sanskrit", "india"),

    # ── 원전 ────────────────────────────────────────────
    "yogacarabhumi":   ("yogacara",    "classical",         "sanskrit", "india"),
    "mulamadhyamakakarika":("madhyamaka","classical",       "sanskrit", "india"),
    "pramanavarttika": ("pramana",     "post_classical",    "sanskrit", "india"),
    "pramanasamuccaya":("pramana",     "classical",         "sanskrit", "india"),
    "vimsatika":       ("yogacara",    "classical",         "sanskrit", "india"),
    "trimsika":        ("yogacara",    "classical",         "sanskrit", "india"),
    "abhidharmakosa":  ("abhidharma",  "classical",         "sanskrit", "india"),
    "yogasutra":       ("yoga",        "classical",         "sanskrit", "india"),
    "yogasutra_bhasya":("yoga",        "classical",         "sanskrit", "india"),
    "bhagavadgita":    ("vedanta",     "upanishadic_sutra", "sanskrit", "india"),
    "upanishad":       ("vedic",       "upanishadic_sutra", "sanskrit", "india"),
    "brahma_sutra":    ("vedanta",     "classical",         "sanskrit", "india"),
    "ratnagotravibhaga":("yogacara",   "classical",         "sanskrit", "india"),
    "bodhisattvabhumi":("yogacara",    "classical",         "sanskrit", "india"),
    "veda":            ("vedic",       "vedic",             "sanskrit", "india"),
}


def backfill(dry_run: bool = False) -> None:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096        # 줄바꿈 자동 폴딩 방지
    yaml.indent(mapping=2, sequence=2, offset=0)

    with CONCEPTS_PATH.open("r", encoding="utf-8") as f:
        data = yaml.load(f)

    n_total = 0
    n_updated = 0
    n_missing = []
    n_renamed_century = 0

    seen_ids = set()
    for entry in data:
        cid = entry.get("canonical_id")
        if not cid:
            continue
        n_total += 1
        seen_ids.add(cid)

        # 기존 free-form era (예: "7세기") → century 로 rename
        existing_era = entry.get("era")
        if existing_era and not _looks_like_bucket(str(existing_era)):
            # ruamel.yaml의 CommentedMap에서는 위치 보존하며 키 교체
            _rename_key(entry, "era", "century")
            n_renamed_century += 1

        meta = METADATA.get(cid)
        if not meta:
            n_missing.append(cid)
            continue

        school, era, source_lang, reception = meta
        # type 다음 위치에 4개 필드 삽입 (이미 있으면 덮어쓰기)
        _insert_after_key(entry, "type",
                          [("school", school),
                           ("era", era),
                           ("source_language", source_lang),
                           ("reception_horizon", reception)])
        n_updated += 1

    print(f"전체 entry: {n_total}")
    print(f"메타필드 추가: {n_updated}")
    print(f"기존 era → century rename: {n_renamed_century}")
    print(f"매핑 미정의: {len(n_missing)}")
    if n_missing:
        for cid in n_missing:
            print(f"  - {cid}")

    # 매핑에는 있지만 데이터에 없는 ID (오타 검출)
    mapping_extras = set(METADATA.keys()) - seen_ids
    if mapping_extras:
        print(f"\n매핑에는 있지만 concepts.yml 에 없는 ID (스크립트 오타 가능):")
        for cid in sorted(mapping_extras):
            print(f"  - {cid}")

    if dry_run:
        print("\n[dry-run] 파일 미저장")
        return

    with CONCEPTS_PATH.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)
    print(f"\n저장 → {CONCEPTS_PATH.relative_to(ROOT)}")


# ============================================================
# helpers — ruamel.yaml CommentedMap 키 순서 조작
# ============================================================

def _looks_like_bucket(s: str) -> bool:
    """이미 새 era bucket 값인지 (rename 스킵)."""
    return s in {"vedic", "upanishadic_sutra", "classical",
                 "post_classical", "late", "modern", "transversal"}


def _rename_key(mapping, old: str, new: str) -> None:
    """CommentedMap 의 키 이름만 변경 (값·위치 보존)."""
    if old not in mapping:
        return
    items = list(mapping.items())
    mapping.clear()
    for k, v in items:
        if k == old:
            mapping[new] = v
        else:
            mapping[k] = v


def _insert_after_key(mapping, anchor_key: str,
                      new_pairs: list[tuple[str, object]]) -> None:
    """`anchor_key` 직후에 (key, value) 쌍들을 삽입.
    이미 같은 키가 있으면 그 위치의 값만 갱신, 새로 삽입은 스킵.
    """
    existing = {k for k in mapping}
    to_insert = [(k, v) for k, v in new_pairs if k not in existing]
    for k, v in new_pairs:
        if k in existing:
            mapping[k] = v
    if not to_insert:
        return
    items = list(mapping.items())
    mapping.clear()
    inserted = False
    for k, v in items:
        mapping[k] = v
        if k == anchor_key and not inserted:
            for nk, nv in to_insert:
                mapping[nk] = nv
            inserted = True
    if not inserted:
        # anchor 없으면 끝에 append
        for nk, nv in to_insert:
            mapping[nk] = nv


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="저장 안 함, 통계만 출력")
    args = p.parse_args()
    try:
        backfill(dry_run=args.dry_run)
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        raise
