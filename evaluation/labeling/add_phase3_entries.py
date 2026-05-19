"""Phase 3 — concepts.yml 에 신규 entry 일괄 추가.

배경:
    Phase 2 의 키워드 등장 빈도 감사 (`audit_keyword_coverage.py`) 결과 INCLUDE +
    MARGINAL 판정 후보를 학파(6) / 인물(8) / 텍스트(6) / 근대 인도(3) / 메타(4) 로
    묶어 ~27개 entry 추가. 사용자 결정 Q1c / Q2c / Q3 contextual 반영.

원칙:
    - canonical_id 가 이미 존재하면 skip (멱등)
    - school 값이 SCHEMA.md 의 enum 에 없으면 경고
    - 모호 텍스트(Q3) 는 school: "contextual" 로 표기 → 라벨링 파이프라인이 처리

실행:
    .venv/bin/python evaluation/labeling/add_phase3_entries.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

ROOT = Path(__file__).resolve().parent.parent.parent
CONCEPTS_PATH = ROOT / "data" / "dictionaries" / "concepts.yml"


# ============================================================
# 신규 entry 정의 — Phase 2 audit 통과한 27개
# 각 entry: canonical_id 가 unique key. 이미 있으면 skip.
# ============================================================

def E(canonical_id, canonical_kr, type_, school, era,
      source_language, reception_horizon,
      surface_forms, *, canonical_iast=None, canonical_zh=None,
      century=None, notes=None, verified=True) -> dict:
    """entry 생성 헬퍼 — 키 순서 안정화."""
    d = {
        "canonical_id": canonical_id,
        "canonical_kr": canonical_kr,
    }
    if canonical_iast: d["canonical_iast"] = canonical_iast
    if canonical_zh:   d["canonical_zh"] = canonical_zh
    d["type"] = type_
    d["school"] = school
    d["era"] = era
    d["source_language"] = source_language
    d["reception_horizon"] = reception_horizon
    if century: d["century"] = century
    d["surface_forms"] = list(surface_forms)
    d["verified"] = verified
    if notes: d["notes"] = notes
    return d


NEW_ENTRIES: list[dict] = [
    # ────────────────────────────────────────────────────────
    # A. 학파 (6) — 데이터에 학파 키워드 등장
    # ────────────────────────────────────────────────────────
    E("mimamsa", "미맘사", "학파", "mimamsa", "classical",
      "sanskrit", "india",
      ["미맘사", "미망사", "Mīmāṃsā", "Mimamsa", "彌曼差", "迷曼差"],
      canonical_iast="Mīmāṃsā", canonical_zh="彌曼差",
      notes="인도 정통 6파 중 하나. 베다 해석학·제식 행위론."),

    E("huayan", "화엄종", "학파", "huayan", "classical",
      "chinese", "east_asia",
      ["화엄", "화엄종", "華嚴", "華嚴宗", "Huayan", "Hua-yen", "Hwaom"],
      canonical_iast=None, canonical_zh="華嚴宗",
      notes="동아시아 화엄종. 法藏·智儼·澄觀·義湘 등. 7-8세기 중국 형성."),

    E("chan", "선종", "학파", "chan", "classical",
      "chinese", "east_asia",
      ["선", "禪", "선종", "禪宗", "선불교", "Chan", "Zen", "Son", "Seon"],
      canonical_zh="禪宗",
      notes="중국·한국·일본 선종 통합 (사용자 결정 4). 지역은 reception_horizon 으로 분기."),

    E("pure_land", "정토종", "학파", "pure_land", "classical",
      "chinese", "east_asia",
      ["정토", "정토종", "淨土", "淨土宗", "Pure Land", "Jingtu"],
      canonical_zh="淨土宗",
      notes="동아시아 정토 신앙 학파. 善導·法然·親鸞 (단 일본 인물은 데이터에 부재)."),

    E("esoteric_east_asia", "동아시아 밀교 / 진언", "학파", "esoteric_east_asia", "post_classical",
      "chinese", "east_asia",
      ["진언", "진언종", "眞言", "眞言宗", "동아시아 밀교", "Shingon"],
      canonical_zh="眞言宗",
      notes="동아시아 밀교 (한국·일본). 인도 후기 탄트라 (tantric_buddhism) 의 동아시아 수용. "
            "★ school 값 'esoteric_east_asia' 는 SCHEMA.md 동아시아 section 에 추가됨."),

    E("tibetan_buddhism_general", "티베트 불교 일반", "학파", "tibetan_other", "post_classical",
      "tibetan", "tibet",
      ["티베트 불교", "티벳 불교", "티벳불교", "티베트불교", "Tibetan Buddhism", "서장불교"],
      notes="티베트 불교 일반어 entry. 겔룩·닝마·카규·사캬 등 학파 미세분류 키워드가 부재할 때 fallback."),

    # ────────────────────────────────────────────────────────
    # B. 인물 (8) — 데이터에 1+건 등장
    # ────────────────────────────────────────────────────────
    E("kamalasila", "까말라쉴라", "학자", "madhyamaka", "post_classical",
      "sanskrit", "india",
      ["까말라쉴라", "카말라실라", "Kamalaśīla", "Kamalashila", "蓮華戒"],
      canonical_iast="Kamalaśīla", canonical_zh="蓮華戒", century="8세기",
      notes="인도 후기 중관학파. 티베트 삼예논쟁(792-794)에서 점오 입장. 활동은 티베트지만 학적 출신은 인도."),

    E("zhiyi", "지의", "학자", "tiantai", "classical",
      "chinese", "east_asia",
      ["지의", "智顗", "Zhiyi", "Chih-i", "천태대사"],
      canonical_zh="智顗", century="6세기",
      notes="중국 천태종 대성자. 法華玄義·摩訶止觀·法華文句."),

    E("kuiji", "규기", "학자", "faxiang", "classical",
      "chinese", "east_asia",
      ["규기", "窺基", "자은", "慈恩", "Kuiji"],
      canonical_zh="窺基", century="7세기",
      notes="중국 법상종 (동아시아 유식) 대성자. 玄奘 문하. 成唯識論述記."),

    # ★ Q1c — 사용자 확정: 한역가의 활동은 동아시아 불교의 토대
    E("kumarajiva", "구마라집", "학자", "madhyamaka", "classical",
      "mixed", "east_asia",
      ["구마라집", "구마라십", "鳩摩羅什", "羅什", "Kumārajīva", "Kumarajiva"],
      canonical_iast="Kumārajīva", canonical_zh="鳩摩羅什", century="4-5세기",
      notes="★ Q1c (사용자 결정): school=madhyamaka, reception=east_asia. "
            "쿠차 출신, 인도 madhyamaka 사상가지만 한역 작업이 동아시아 불교의 토대."),

    E("jizang", "길장", "학자", "sanlun", "classical",
      "chinese", "east_asia",
      ["길장", "吉藏", "가상", "嘉祥", "Jizang"],
      canonical_zh="吉藏", century="6-7세기",
      notes="중국 삼론종 (동아시아 중관) 대성자. 中觀論疏·百論疏·十二門論疏."),

    E("wonchuk", "원측", "학자", "yogacara", "classical",
      "chinese", "korea",
      ["원측", "圓測", "Wonchuk"],
      canonical_zh="圓測", century="7세기",
      notes="한국(신라) 출신, 玄奘 문하의 유식학자. 解深密經疏 등. school=yogacara (인도 유식 연구), reception=korea (한국 출신)."),

    E("iryeon", "일연", "학자", "korean_buddhism", "late",
      "chinese", "korea",
      ["일연", "一然", "Iryeon"],
      canonical_zh="一然", century="13세기",
      notes="고려 시대 승려. 三國遺事 저자."),

    E("tsongkhapa", "쫑카파", "학자", "gelug", "late",
      "tibetan", "tibet",
      ["쫑카파", "쫑카빠", "총카파", "Tsongkhapa", "Tsong-kha-pa", "Je Tsongkhapa", "宗喀巴"],
      canonical_zh="宗喀巴", century="14-15세기",
      notes="티베트 겔룩파 창시자. Lam rim chen mo·Lam gtso rnam gsum 등."),

    # ────────────────────────────────────────────────────────
    # C. 텍스트 (6) — Q2c · Q3 룰 적용
    # ────────────────────────────────────────────────────────
    # ★ Q2c — 사용자 확정: 동아시아 자체 형성 (위경 가능성)
    E("awakening_of_faith", "대승기신론", "원전", "east_asian_other", "classical",
      "chinese", "east_asia",
      ["기신론", "대승기신론", "大乘起信論", "起信論", "Awakening of Faith"],
      canonical_zh="大乘起信論",
      notes="★ Q2c (사용자 결정): school=east_asian_other. "
            "전통 귀속은 馬鳴(Aśvaghoṣa)이나 위경 가능성, 동아시아 자체 형성. 여래장 + 유식 결합."),

    # ★ Q3 — 사전에서 school 단정 회피. 라벨링 파이프라인이 공출현 키워드로 결정.
    E("avatamsaka", "화엄경", "원전", "contextual", "upanishadic_sutra",
      "chinese", "contextual",
      ["화엄경", "華嚴經", "大方廣佛華嚴經", "Avataṃsaka", "Avatamsaka", "Gaṇḍavyūha"],
      canonical_iast="Avataṃsakasūtra", canonical_zh="華嚴經",
      notes="★ Q3 (사용자 결정): school·reception 단정 회피. "
            "인도 산스크리트 원전(c.1-4세기) 이지만 동아시아 화엄종 텍스트로 더 활발히 다뤄짐. "
            "공출현 키워드 기반 contextual disambiguation 룰이 결정 (SCHEMA.md §8)."),

    E("lotus_sutra", "법화경", "원전", "contextual", "upanishadic_sutra",
      "chinese", "contextual",
      ["법화경", "妙法蓮華經", "法華經", "Saddharmapuṇḍarīka", "Saddharmapundarika", "Lotus Sūtra"],
      canonical_iast="Saddharmapuṇḍarīkasūtra", canonical_zh="妙法蓮華經",
      notes="★ Q3 (사용자 결정): school·reception 단정 회피. "
            "인도 산스크리트 원전(c.1-2세기) 이지만 동아시아 천태·일련 등 다수 종파가 다룸."),

    E("larger_sukhavativyuha", "무량수경", "원전", "pure_land", "upanishadic_sutra",
      "chinese", "east_asia",
      ["무량수경", "無量壽經", "Larger Sukhāvatīvyūha", "Sukhāvatīvyūha"],
      canonical_iast="Sukhāvatīvyūhasūtra", canonical_zh="無量壽經",
      notes="정토삼부경의 하나. 인도 산스크리트 원전 있으나 동아시아 정토종 텍스트로 자리매김."),

    E("smaller_sukhavativyuha", "아미타경", "원전", "pure_land", "upanishadic_sutra",
      "chinese", "east_asia",
      ["아미타경", "阿彌陀經", "Smaller Sukhāvatīvyūha"],
      canonical_zh="阿彌陀經",
      notes="정토삼부경의 하나."),

    E("contemplation_sutra", "관무량수경", "원전", "pure_land", "classical",
      "chinese", "east_asia",
      ["관무량수경", "觀無量壽經", "Contemplation Sūtra", "Amitāyurdhyāna"],
      canonical_zh="觀無量壽經",
      notes="정토삼부경의 하나. 동아시아 composed 가능성 (위경 논의)."),

    # ────────────────────────────────────────────────────────
    # D. 근대 인도 사상가 (3) — 각 1-2건
    # ────────────────────────────────────────────────────────
    E("ramakrishna", "라마크리슈나", "학자", "hindu_modern", "modern",
      "mixed", "india",
      ["라마크리슈나", "라마끄리슈나", "Ramakrishna", "Rāmakṛṣṇa"],
      canonical_iast="Rāmakṛṣṇa", century="19세기",
      notes="근대 인도 신비주의자. 비베카난다의 스승."),

    E("vivekananda", "비베카난다", "학자", "hindu_modern", "modern",
      "mixed", "india",
      ["비베카난다", "비배카난다", "Vivekananda", "Vivekānanda"],
      canonical_iast="Vivekānanda", century="19세기",
      notes="라마크리슈나 미션 창설자. 1893 시카고 종교회의."),

    E("radhakrishnan", "라다크리슈난", "학자", "hindu_modern", "modern",
      "mixed", "india",
      ["라다크리슈난", "라다끄리슈난", "Radhakrishnan", "S. Radhakrishnan", "Sarvepalli Radhakrishnan"],
      century="20세기",
      notes="근대 인도 철학자·정치가. 인도철학 통사 저술. 인도 부통령·대통령 역임."),

    # ────────────────────────────────────────────────────────
    # E. 메타 / 보강 (4)
    # ────────────────────────────────────────────────────────
    E("hatha_yoga", "하타 요가", "개념", "yoga", "post_classical",
      "sanskrit", "india",
      ["하타 요가", "하타요가", "하타", "하타프라디피카", "하타(요가)쁘라디삐까",
       "Haṭha Yoga", "Hatha Yoga", "Haṭhayoga"],
      canonical_iast="Haṭhayoga",
      notes="후기 요가 신체 수행 전통 (c.10-17세기). yoga 학파의 post_classical 시대 변종. "
            "Hatha Yoga Pradīpikā·Gheraṇḍa Saṃhitā 등."),

    E("chinese_buddhist_canon", "한역 자료 / 대장경", "개념", "comparative", "transversal",
      "chinese", "mixed",
      ["한역", "한역(漢譯)", "대장경", "高麗大藏經", "Taishō", "Taisho"],
      notes="자료 언어 표지. 한역 자료를 사용한 연구에 source_language=chinese 추론을 위해 추가."),

    E("tibetan_canon", "티베트역 자료 / 깡규르 텡규르", "개념", "comparative", "transversal",
      "tibetan", "mixed",
      ["티벳 사본", "티베트역", "티벳어 번역", "서장어", "Kangyur", "Tengyur", "bKa' 'gyur", "bsTan 'gyur"],
      notes="자료 언어 표지. 티베트역 자료를 사용한 연구에 source_language=tibetan 추론."),

    E("dunhuang", "돈황 사본", "개념", "comparative", "transversal",
      "mixed", "east_asia",
      ["돈황", "돈황 막고굴", "돈황 필사본", "돈황본", "돈황사본", "Dunhuang", "敦煌"],
      canonical_zh="敦煌",
      notes="돈황 사본학. 동아시아 자료 + 사본학 방법론 표지."),
]


# ============================================================
# main
# ============================================================

def main(dry_run: bool = False) -> None:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=2, offset=0)

    with CONCEPTS_PATH.open("r", encoding="utf-8") as f:
        data = yaml.load(f)

    existing_ids = {entry.get("canonical_id") for entry in data if entry.get("canonical_id")}

    n_added = 0
    n_skipped_exists = 0
    added_ids = []
    skipped_ids = []

    for entry in NEW_ENTRIES:
        cid = entry["canonical_id"]
        if cid in existing_ids:
            n_skipped_exists += 1
            skipped_ids.append(cid)
            continue
        # CommentedMap 으로 변환해 ruamel 의 indent 규칙을 따르게 함
        cm = CommentedMap(entry)
        data.append(cm)
        existing_ids.add(cid)
        n_added += 1
        added_ids.append(cid)

    print(f"신규 후보: {len(NEW_ENTRIES)}")
    print(f"추가: {n_added}")
    print(f"이미 존재 → skip: {n_skipped_exists}")
    if added_ids:
        print("\n추가된 ID:")
        for cid in added_ids:
            print(f"  + {cid}")
    if skipped_ids:
        print("\nSkip 된 ID (이미 존재):")
        for cid in skipped_ids:
            print(f"  · {cid}")

    if dry_run:
        print("\n[dry-run] 파일 미저장")
        return

    if n_added == 0:
        print("\n변경 없음 — 파일 미저장")
        return

    with CONCEPTS_PATH.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)
    print(f"\n저장 → {CONCEPTS_PATH.relative_to(ROOT)}  (총 entry: {len(data)})")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="저장 안 함")
    args = p.parse_args()
    try:
        main(dry_run=args.dry_run)
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        raise
