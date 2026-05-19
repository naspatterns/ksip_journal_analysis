"""Phase 5 환류 (사전 보강) — authors.yml 의 각 entry 에 `horizon` 메타 추가.

배경:
    Phase 4.4 의 `detect_secondary_horizon` 이 학술지 publisher 매칭 + Unicode
    dominance fallback 으로 작동. 그러나 한국 학자가 일본 학자의 한국어 번역서를
    인용하는 경우 Hangul 우세로 korean 으로 분류됨 (예: 정토삼부경/中村元/岩波文庫).
    실제 학적 영향은 일본 학계. authors.yml 에 `horizon` 명시하면 저자 매칭 시
    그 학자의 학계로 horizon 결정 가능 → 정확도 ↑.

값:
    horizon ∈ {korean, japanese, english, german, french}

원칙:
    - 학자의 publication-language / 학적 활동 무대 기준
    - Schmithausen (Hamburg/Germany) → german
    - Bronkhorst (Lausanne/Swiss but publishes English) → english
    - Halbfass (Penn US but German-trained, major works in German) → german
    - 인도계 영문 학자 (Olivelle/Cardona/Rukmani/Seyfort Ruegg/Sanderson/
      Radhakrishnan/Gerow) → english

실행:
    .venv/bin/python evaluation/labeling/add_authors_horizon.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parent.parent.parent
AUTHORS_PATH = ROOT / "data" / "dictionaries" / "authors.yml"


# canonical_id → horizon
HORIZON_BY_ID: dict[str, str] = {
    # ── 한국 학자 (28) ─────────────────────────────────────────
    "jeong_seungseok": "korean",
    "lee_jisoo": "korean",
    "lee_taeseung": "korean",
    "kim_hosung": "korean",
    "park_hyoyeop": "korean",
    "ahn_seongdu": "korean",
    "kim_seongchul": "korean",
    "hwang_soonil": "korean",
    "kim_seonkun": "korean",
    "park_giyeol": "korean",
    "kwon_omin": "korean",
    "kim_seongok": "korean",
    "kim_jaegwon": "korean",
    "jeon_jaeseong": "korean",
    "park_yeonggil": "korean",
    "jeong_taehyeok": "korean",
    "im_seungtaek": "korean",
    "ryu_hyeonjeong": "korean",
    "shim_junbo": "korean",
    "kim_jaeseong": "korean",
    "im_geundong": "korean",
    "yang_yeongsoon": "korean",
    "kim_jaemin": "korean",
    "nam_sooyoung": "korean",
    "kang_seongyong": "korean",
    "kang_hyeongchul": "korean",
    "gakmuk_sunim": "korean",
    "daerim_sunim": "korean",

    # ── 일본 학자 (13) ─────────────────────────────────────────
    "hirakawa_akira": "japanese",
    "nagao_gajin": "japanese",
    "nakamura_hajime": "japanese",
    "takasaki_jikido": "japanese",
    "tosaki_hiromasa": "japanese",
    "kajiyama_yuichi": "japanese",
    "yamaguchi_susumu": "japanese",
    "katsura_shoryu": "japanese",
    "fujita_kotatsu": "japanese",
    "mizuno_kogen": "japanese",
    "ui_hakuju": "japanese",
    "wogihara_unrai": "japanese",
    "kajihara_mieko": "japanese",

    # ── 영어권 학자 (8) — 독일/스위스 출신이지만 영어로 출판하는 학자 포함 ──
    "bronkhorst_johannes": "english",      # Lausanne Swiss, 영어 출판 중심
    "olivelle_patrick": "english",         # UT Austin
    "rukmani_ts": "english",               # Indian-Canadian
    "seyfort_ruegg": "english",            # Belgium-born, UK/US 활동
    "sanderson_alexis": "english",         # Oxford
    "cardona_george": "english",           # U Penn
    "radhakrishnan_s": "english",          # Indian philosopher, EN 출판
    "gerow_edwin": "english",              # Reed College US

    # ── 독일어권 학자 (2) ────────────────────────────────────
    "schmithausen_lambert": "german",      # Hamburg, 독일어/영어 양수
    "halbfass_wilhelm": "german",          # Penn 활동이나 독일 훈련, 주저는 독일어 (Indien und Europa)

    # ── 프랑스어권 학자 (1) ──────────────────────────────────
    "levi_sylvain": "french",              # Sylvain Lévi, 프랑스 인도학자
}


def _make_yaml() -> YAML:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096
    return yaml


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not AUTHORS_PATH.exists():
        print(f"❌ authors.yml not found at {AUTHORS_PATH}", file=sys.stderr)
        return 1

    yaml = _make_yaml()
    with AUTHORS_PATH.open("r", encoding="utf-8") as f:
        data = yaml.load(f)

    if not isinstance(data, list):
        print(f"❌ 최상위 구조가 list 가 아님", file=sys.stderr)
        return 1

    total = len(data)
    added = 0
    already_has = 0
    missing_mapping: list[str] = []
    mismatch_id: list[str] = []

    yaml_ids = set()
    for entry in data:
        cid = entry.get("canonical_id")
        if not cid:
            continue
        yaml_ids.add(cid)
        if cid not in HORIZON_BY_ID:
            missing_mapping.append(cid)
            continue
        horizon = HORIZON_BY_ID[cid]
        if "horizon" in entry:
            if entry["horizon"] == horizon:
                already_has += 1
                continue
            else:
                print(f"⚠️  [{cid}] 기존 horizon={entry['horizon']!r} → 새값 {horizon!r} 로 덮어쓰기",
                      file=sys.stderr)
                entry["horizon"] = horizon
                added += 1
                continue
        # surface_forms 앞에 horizon 삽입
        keys = list(entry.keys())
        if "surface_forms" in keys:
            idx = keys.index("surface_forms")
        else:
            # 끝에 붙임
            idx = len(keys)
        entry.insert(idx, "horizon", horizon)
        added += 1

    # 매핑에는 있는데 yaml 에 없는 id
    mapping_orphans = sorted(set(HORIZON_BY_ID.keys()) - yaml_ids)

    print(f"=== 통계 (authors.yml, {total} entry) ===")
    print(f"  horizon 추가         : {added}")
    print(f"  이미 보유 (no-op)    : {already_has}")
    print(f"  매핑 미정의 (skip)   : {len(missing_mapping)}")
    if missing_mapping:
        for cid in missing_mapping:
            print(f"    - {cid}")
    if mapping_orphans:
        print(f"\n  매핑에 있으나 YAML 에 없음 (확인 필요): {len(mapping_orphans)}")
        for cid in mapping_orphans:
            print(f"    - {cid}")

    if args.dry_run:
        print("\n[dry-run] 파일 변경 안 함.")
        return 0
    if added == 0:
        print("\n변경 사항 없음.")
        return 0

    with AUTHORS_PATH.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)

    print(f"\n✅ {AUTHORS_PATH.relative_to(ROOT)} 저장 완료 ({added} entry horizon 추가).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
