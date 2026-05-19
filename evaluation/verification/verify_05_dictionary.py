"""L6 — Dictionary (Authority Control) 내부 일관성.

확인:
- 모든 entry 가 unique canonical_id
- entry 내 surface_forms 중복 없음
- entry 간 중복 surface (last-wins 의도? 사고?)
- school/era/tradition_language/reception_horizon 값이 SCHEMA enum 안
- verified=true entry 가 모든 분류 메타필드 보유
- Phase 3 신규 27 entry 가 모두 로드
- contextual school 값이 의도한 entry 에만 부착 (Q3 룰)
"""
from __future__ import annotations

import sys
import unicodedata
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import ksip.normalize  # noqa: E402
from ksip.normalize import load_authority  # noqa: E402

from _common import DICT_DIR, CheckRun, ensure_output_dir


# SCHEMA.md 의 enum
SCHOOL_VALUES = {
    # 인도
    "samkhya", "yoga", "nyaya", "vaisheshika", "mimamsa", "vedanta",
    "abhidharma", "madhyamaka", "yogacara", "pramana", "tantric_buddhism",
    "jainism", "charvaka", "hindu_modern", "sikh", "vedic",
    # 동아시아
    "huayan", "tiantai", "chan", "pure_land", "faxiang", "sanlun",
    "tendai_japan", "shingon", "esoteric_east_asia", "nichiren",
    "korean_buddhism", "east_asian_other",
    # 티베트
    "gelug", "nyingma", "kagyu", "sakya", "bon", "tibetan_other",
    # 그 외
    "comparative", "meta", "contextual", "unclassified",
}

ERA_VALUES = {"vedic", "upanishadic_sutra", "classical", "post_classical",
              "late", "modern", "transversal"}

TRADITION_LANG_VALUES = {"sanskrit", "pali", "prakrit", "chinese", "tibetan",
                         "modern_korean", "mixed", "n/a"}

RECEPTION_VALUES = {"india", "east_asia", "tibet", "korea", "west", "mixed",
                    "contextual"}

# Phase 3 에서 추가된 entry
PHASE3_IDS = {
    "mimamsa", "huayan", "chan", "pure_land", "esoteric_east_asia",
    "tibetan_buddhism_general", "kamalasila", "zhiyi", "kuiji", "kumarajiva",
    "jizang", "wonchuk", "iryeon", "tsongkhapa", "awakening_of_faith",
    "avatamsaka", "lotus_sutra", "larger_sukhavativyuha",
    "smaller_sukhavativyuha", "contemplation_sutra", "ramakrishna",
    "vivekananda", "radhakrishnan", "hatha_yoga", "chinese_buddhist_canon",
    "tibetan_canon", "dunhuang",
}
# Q3 contextual entry — school==contextual 가 의도된 곳
CONTEXTUAL_INTENDED = {"avatamsaka", "lotus_sutra"}


def _nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s).strip()


def _check_yaml(yml_path: Path, run: CheckRun, name: str) -> dict:
    """단일 yml 파일의 내부 일관성 검증. 로드된 raw data 반환."""
    with yml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []

    ids = [e.get("canonical_id") for e in data]
    n = len(data)

    # 1) canonical_id null
    null_ids = sum(1 for i in ids if not i)
    if null_ids:
        run.fatal(f"{name}_null_id",
                  f"{name}.yml: canonical_id 가 비어있는 entry {null_ids}건",
                  n_affected=null_ids)
    else:
        run.pass_(f"{name}_null_id", f"{name}.yml: 모든 entry 에 canonical_id")

    # 2) canonical_id 중복
    dup = [i for i, c in Counter(ids).items() if c > 1 and i]
    if dup:
        run.fatal(f"{name}_dup_id",
                  f"{name}.yml: canonical_id 중복 {len(dup)}건 — {dup[:5]}",
                  n_affected=len(dup))
    else:
        run.pass_(f"{name}_dup_id",
                  f"{name}.yml: canonical_id 모두 unique (n={n})")

    # 3) entry 내 surface_forms 중복
    intra_dup = 0
    for e in data:
        sfs = e.get("surface_forms", []) or []
        nfkc_sfs = [_nfkc(s).lower() for s in sfs]
        if len(nfkc_sfs) != len(set(nfkc_sfs)):
            intra_dup += 1
    if intra_dup:
        run.warn(f"{name}_intra_surface_dup",
                 f"{name}.yml: entry 내 surface_forms 중복 {intra_dup}건",
                 n_affected=intra_dup)
    else:
        run.pass_(f"{name}_intra_surface_dup",
                  f"{name}.yml: entry 내 surface 중복 없음")

    # 4) entry 간 surface 중복 (last-wins 가 의도된 곳)
    surface_to_cids: dict[str, list[str]] = {}
    for e in data:
        cid = e.get("canonical_id")
        for s in e.get("surface_forms", []) or []:
            k = _nfkc(s).lower()
            if not k:
                continue
            surface_to_cids.setdefault(k, []).append(cid)
    inter_dup = {k: v for k, v in surface_to_cids.items() if len(v) > 1}
    if inter_dup:
        run.warn(f"{name}_inter_surface_dup",
                 f"{name}.yml: 여러 entry 가 공유하는 surface {len(inter_dup)}건 — "
                 f"normalize.py 는 last-wins. 예: "
                 f"{list(inter_dup.items())[:3]}",
                 n_affected=len(inter_dup))
    else:
        run.pass_(f"{name}_inter_surface_dup",
                  f"{name}.yml: entry 간 surface 중복 없음")

    return data


def main() -> int:
    run = CheckRun("L6")

    # concepts.yml 가 가장 핵심 — 신규 메타필드 검증
    ksip.normalize.load_authority.cache_clear()
    concepts_yml = DICT_DIR / "concepts.yml"
    data = _check_yaml(concepts_yml, run, "concepts")

    # concepts.yml entry 수
    run.info("concepts_total", f"concepts.yml entry 총 {len(data)}개",
             n_affected=len(data))

    # Phase 3 의 27개 entry 가 모두 있는가
    seen_ids = {e.get("canonical_id") for e in data}
    missing_p3 = PHASE3_IDS - seen_ids
    if missing_p3:
        run.fatal("phase3_missing",
                  f"Phase 3 신규 entry {len(missing_p3)}개 누락: {sorted(missing_p3)}",
                  n_affected=len(missing_p3))
    else:
        run.pass_("phase3_present",
                  f"Phase 3 27 entry 모두 존재")

    # verified=true entry 가 분류 4필드 보유 여부
    bad_school = bad_era = bad_src = bad_rec = 0
    contextual_unexpected = []
    school_enum_violations = []
    era_enum_violations = []
    src_enum_violations = []
    rec_enum_violations = []
    for e in data:
        if not e.get("verified"):
            continue
        cid = e.get("canonical_id")
        school = e.get("school")
        era = e.get("era")
        src = e.get("tradition_language")
        rec = e.get("reception_horizon")

        if not school: bad_school += 1
        elif school not in SCHOOL_VALUES:
            school_enum_violations.append((cid, school))
        if not era: bad_era += 1
        elif era not in ERA_VALUES:
            era_enum_violations.append((cid, era))
        if not src: bad_src += 1
        elif src not in TRADITION_LANG_VALUES:
            src_enum_violations.append((cid, src))
        if not rec: bad_rec += 1
        elif rec not in RECEPTION_VALUES:
            rec_enum_violations.append((cid, rec))

        # contextual 사용처 검증
        if school == "contextual" and cid not in CONTEXTUAL_INTENDED:
            contextual_unexpected.append(cid)

    for fld, missing in [("school", bad_school), ("era", bad_era),
                         ("tradition_language", bad_src),
                         ("reception_horizon", bad_rec)]:
        if missing:
            run.warn(f"verified_missing_{fld}",
                     f"verified=true entry 에 {fld} 누락 {missing}건",
                     n_affected=missing)
        else:
            run.pass_(f"verified_has_{fld}",
                      f"verified entry 모두 {fld} 보유")

    for fld, viol, enum_name in [
        ("school", school_enum_violations, "SCHOOL_VALUES"),
        ("era", era_enum_violations, "ERA_VALUES"),
        ("tradition_language", src_enum_violations, "TRADITION_LANG_VALUES"),
        ("reception_horizon", rec_enum_violations, "RECEPTION_VALUES"),
    ]:
        if viol:
            run.warn(f"enum_violation_{fld}",
                     f"{fld} enum 위반 {len(viol)}건 — 예: {viol[:3]}",
                     n_affected=len(viol))
        else:
            run.pass_(f"enum_valid_{fld}",
                      f"{fld} 값 모두 enum 안")

    if contextual_unexpected:
        run.warn("contextual_unexpected",
                 f"contextual school 이 의도(avatamsaka/lotus_sutra) 외에 부착됨: {contextual_unexpected}",
                 n_affected=len(contextual_unexpected))
    else:
        run.pass_("contextual_intended",
                  "contextual school 이 의도된 entry 에만 부착")

    # contextual 의도된 entry 가 실제 contextual 인지
    contextual_actual = {e.get("canonical_id") for e in data
                         if e.get("school") == "contextual"}
    missing_contextual = CONTEXTUAL_INTENDED - contextual_actual
    if missing_contextual:
        run.warn("contextual_intended_missing",
                 f"Q3 의도 entry 가 contextual school 미부착: {missing_contextual}",
                 n_affected=len(missing_contextual))
    else:
        run.pass_("contextual_intended_match",
                  f"Q3 의도 entry {CONTEXTUAL_INTENDED} 가 contextual school 부착됨")

    # 다른 사전들도 점검 (간단)
    for name in ["authors", "journals", "institutions"]:
        p = DICT_DIR / f"{name}.yml"
        if p.exists():
            _check_yaml(p, run, name)

    # normalize.py 로 실제 로드 가능 여부
    try:
        auth = load_authority("concepts", include_unverified=True)
        run.info("concepts_loadable_inc_unverified",
                 f"include_unverified=True 로 {len(auth.records)} entry 로드됨",
                 n_affected=len(auth.records))
    except Exception as e:
        run.fatal("concepts_loadable", f"normalize.load_authority 실패: {e}")

    run.print_summary()
    run.to_csv(ensure_output_dir() / "verify_05_dictionary.csv")
    return 1 if run.counts()["FATAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
