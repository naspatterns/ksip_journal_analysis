"""데이터 품질 진단 — 어디에 어떤 클리닝이 필요한지 한 번에 점검.

각 섹션은 (1) 문제 패턴 (2) 영향 받는 행 수 (3) 대표 사례 / TOP 변형을 출력.
실제 클리닝은 별도(ksip/clean.py 등)에서 사용자 합의 후 적용.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PROC = ROOT / "data" / "processed"

papers = pd.read_parquet(PROC / "papers.parquet")
authors = pd.read_parquet(PROC / "authors.parquet")
keywords = pd.read_parquet(PROC / "keywords.parquet")
refs = pd.read_parquet(PROC / "references.parquet")

W = 78
def section(title: str) -> None:
    print()
    print("=" * W)
    print(f"  {title}")
    print("=" * W)


def sub(title: str) -> None:
    print(f"\n— {title} —")


# ════════════════════════════════════════════════════════════════════
# A. 기관명 (주저자 소속기관) 진단
# ════════════════════════════════════════════════════════════════════
section("A. 기관명 — 동일 모기관 분리 / 표기 변형")

inst = papers["주저자 소속기관"].fillna("(미기재)")
print(f"총 행: {len(papers):,}, 미기재: {(inst == '(미기재)').sum()}")
print(f"unique 기관명: {inst.nunique()}")

# A-1. 대학교 family rollup 진단
sub("A-1. 대학교 family — 같은 대학교의 하위 단위 분리 사례")
def parent_university(s: str) -> str | None:
    """문자열에서 첫 '대학교'까지를 부모 기관으로 추출."""
    m = re.match(r"^(.+?대학교)\b", s)
    return m.group(1) if m else None

inst_counts = inst.value_counts()
parent_groups: dict[str, list[tuple[str, int]]] = defaultdict(list)
for name, n in inst_counts.items():
    p = parent_university(name)
    if p:
        parent_groups[p].append((name, int(n)))

# 분리되어 있는 family TOP 10
multi_unit_parents = sorted(
    [(p, members) for p, members in parent_groups.items() if len(members) > 1],
    key=lambda x: -sum(n for _, n in x[1]),
)
print(f"\n  분리된 대학교 family: {len(multi_unit_parents)} 곳")
for p, members in multi_unit_parents[:10]:
    total = sum(n for _, n in members)
    print(f"\n  ▸ {p}  (합산 {total}편, 현재 {len(members)} 변형으로 분리)")
    for name, n in sorted(members, key=lambda x: -x[1]):
        print(f"      {n:>3} · {name}")

# A-2. 영문/약칭 동의어 후보
sub("A-2. 동일 기관 영문/약칭 의심")
all_names = inst_counts.index.tolist()
# Korean 'X대학교' vs English 'X University'
for kr_token in ["동국", "서울", "고려", "연세", "성균관", "경북", "부산", "전남", "충남", "위덕", "한국학", "금강"]:
    matches = [n for n in all_names if kr_token in n]
    if len(matches) >= 2:
        print(f"  '{kr_token}' 포함 변형:")
        for m in matches[:6]:
            print(f"      {inst_counts[m]:>3} · {m}")

# A-3. 약자(대학원·연구소·학과 등) 빈도
sub("A-3. 부속 단위 키워드 빈도")
suffix_counts = Counter()
SUFFIXES = ["대학원", "연구소", "연구원", "학부", "학과", "단과대학", "전문대학원",
            "교양교육연구소", "불교문화연구원", "BK21"]
for name in all_names:
    for suf in SUFFIXES:
        if suf in name:
            suffix_counts[suf] += inst_counts[name]
            break  # one suffix per name
for suf, n in suffix_counts.most_common():
    print(f"  {suf:20s} {n:>4} 편이 이 부속 단위 표기 사용")


# ════════════════════════════════════════════════════════════════════
# B. 저자명 (논문목록 측) 진단
# ════════════════════════════════════════════════════════════════════
section("B. 저자명 — 표기 변형 / 동명이인 의심")

print(f"총 author 행: {len(authors):,}, unique surface: {authors['저자_원본'].nunique()}")

# B-1. 한자 부속, 괄호, 영문 알파벳
sub("B-1. 특수 문자 패턴")
patterns = {
    "한자 부속(괄호)": r"[\(（].*[一-鿿].*[\)）]",
    "한글+한자 연속": r"[가-힣]+[一-鿿]",
    "영문 알파벳 포함": r"[A-Za-z]",
    "쉼표 / 마침표 등": r"[,.]",
    "공백 2개 이상": r"\s{2,}",
}
for label, pat in patterns.items():
    n = authors["저자_원본"].str.contains(pat, regex=True, na=False).sum()
    if n > 0:
        sample = authors.loc[authors["저자_원본"].str.contains(pat, regex=True, na=False),
                             "저자_원본"].drop_duplicates().head(5).tolist()
        print(f"  {label:20s} {n:>3} 행 — 예: {sample}")

# B-2. 양 끝 공백 / 정규화
sub("B-2. 유니코드/공백 정규화 효과")
def nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s).strip() if isinstance(s, str) else s
trimmed = authors["저자_원본"].map(nfkc)
n_changed = (trimmed != authors["저자_원본"]).sum()
print(f"  NFKC + strip 후 surface가 변경되는 행: {n_changed}")
if n_changed > 0:
    diff = authors[trimmed != authors["저자_원본"]].head(5)
    for _, r in diff.iterrows():
        print(f"      {r['저자_원본']!r}  →  {nfkc(r['저자_원본'])!r}")

# B-3. 유사 이름 클러스터 (편집거리 1)
sub("B-3. 동명이인 의심 (편집거리 1, 첫 글자 동일)")
unique_names = sorted(authors["저자_원본"].unique())
def dist1(a: str, b: str) -> bool:
    if abs(len(a) - len(b)) > 1:
        return False
    if a == b:
        return False
    if a[0] != b[0]:
        return False
    # naive Levenshtein <= 1
    if len(a) == len(b):
        diffs = sum(1 for x, y in zip(a, b) if x != y)
        return diffs == 1
    longer, shorter = (a, b) if len(a) > len(b) else (b, a)
    for i in range(len(longer)):
        if longer[:i] + longer[i+1:] == shorter:
            return True
    return False

clusters = []
seen = set()
for i, n1 in enumerate(unique_names):
    if n1 in seen:
        continue
    matches = [n2 for n2 in unique_names[i+1:] if dist1(n1, n2)]
    if matches:
        clusters.append([n1] + matches)
        seen.update([n1] + matches)
print(f"  편집거리 1 클러스터: {len(clusters)} 개")
for c in clusters[:10]:
    print(f"      {c}")


# ════════════════════════════════════════════════════════════════════
# C. 키워드 진단
# ════════════════════════════════════════════════════════════════════
section("C. 키워드 — surface form 클리닝 후보")

print(f"총 keyword 행: {len(keywords):,}, unique surface: {keywords['키워드_원본'].nunique()}")

# C-1. 길이 분포
sub("C-1. 길이 분포 (이상치)")
lens = keywords["키워드_원본"].str.len()
for label, mask in [
    ("길이 1자",  lens == 1),
    ("길이 2자",  lens == 2),
    ("길이 30자 초과", lens > 30),
]:
    n = mask.sum()
    if n > 0:
        sample = keywords.loc[mask, "키워드_원본"].value_counts().head(8).index.tolist()
        print(f"  {label:14s} {n:>4} 행 — 예: {sample}")

# C-2. 케이스/공백 변형
sub("C-2. 영문 대소문자 + 공백 변형으로 분리되는 키워드")
def kw_norm(s: str) -> str:
    return unicodedata.normalize("NFKC", str(s)).lower().strip()

norm_groups = defaultdict(list)
for kw, n in keywords["키워드_원본"].value_counts().items():
    norm_groups[kw_norm(kw)].append((kw, int(n)))

multi_form = sorted(
    [(k, v) for k, v in norm_groups.items() if len(v) > 1],
    key=lambda x: -sum(n for _, n in x[1]),
)
print(f"  대소문자/공백/유니코드만 다른 그룹: {len(multi_form)} 개")
for nk, members in multi_form[:8]:
    total = sum(n for _, n in members)
    parts = ", ".join(f"{k!r}({n})" for k, n in members)
    print(f"      [{total} 합산] {parts}")

# C-3. 특수 문자 / mojibake
sub("C-3. 특수 문자 / 깨짐 의심")
mojibake_pat = r"[-￿-]"  # PUA / 사용자 영역
mb = keywords[keywords["키워드_원본"].str.contains(mojibake_pat, regex=True, na=False)]
print(f"  사적 사용 영역(PUA) 문자 포함: {len(mb)} 행")
if len(mb) > 0:
    for k in mb["키워드_원본"].drop_duplicates().head(5):
        print(f"      {k!r}")


# ════════════════════════════════════════════════════════════════════
# D. 논문명/제목 진단
# ════════════════════════════════════════════════════════════════════
section("D. 논문명 — 트레일링 잡문자 / 언더스코어")

# D-1. 끝에 깨진 문자
sub("D-1. 제목 끝 비표준 문자 (PUA, 연속 underscore 등)")
title_pua = papers[papers["논문명"].astype(str).str.contains(mojibake_pat, regex=True, na=False)]
print(f"  PUA 문자 포함: {len(title_pua)} 행")
if len(title_pua) > 0:
    for t in title_pua["논문명"].head(5):
        print(f"      …{repr(t[-40:])}")

trailing_under = papers[papers["논문명"].astype(str).str.match(r".*_+$")]
print(f"  끝이 언더스코어로 끝나는 제목: {len(trailing_under)} 행")
if len(trailing_under) > 0:
    for t in trailing_under["논문명"].head(5):
        print(f"      …{t[-30:]}")


# ════════════════════════════════════════════════════════════════════
# E. 발행 메타 진단 (연도, 권, 호)
# ════════════════════════════════════════════════════════════════════
section("E. 발행 메타 — 연도/권/호 이상")

sub("E-1. 발행연도 분포")
yc = papers["발행연도"].value_counts().sort_index()
print(f"  연도 범위: {yc.index.min()} – {yc.index.max()}")
print(f"  최소 편수 연도: {yc.idxmin()} ({yc.min()}편)")
print(f"  최다 편수 연도: {yc.idxmax()} ({yc.max()}편)")
print(f"  연도 NaN/0: {(papers['발행연도'] == 0).sum() + papers['발행연도'].isna().sum()}")

sub("E-2. 권/호 결측 / 이상")
print(f"  권 NaN: {papers['권'].isna().sum()} / {len(papers)}")
print(f"  호 NaN: {papers['호'].isna().sum()} / {len(papers)}")
print(f"  특별호 표시 있음: {(papers['특별호'].fillna('') != '').sum()}")


# ════════════════════════════════════════════════════════════════════
# F. 참고문헌 파싱 품질
# ════════════════════════════════════════════════════════════════════
section("F. 참고문헌 — 파싱 품질 / 추출 실패 패턴")

print(f"총 reference 행: {len(refs):,}")

sub("F-1. 유형별 추출 품질 (필드 채워진 비율)")
for type_name, type_df in refs.groupby("유형"):
    n = len(type_df)
    cols = ["저자_원본", "제목_원본", "학술지_원본", "연도"]
    rates = {}
    for c in cols:
        if c == "연도":
            rates[c] = type_df[c].notna().sum() / n
        else:
            v = type_df[c].fillna("").str.strip()
            rates[c] = (v != "").sum() / n
    rate_str = " / ".join(f"{c.replace('_원본','')}={r:.0%}" for c, r in rates.items())
    print(f"  {type_name:18s} ({n:>5}건)  {rate_str}")

sub("F-2. 학술지 type인데 학술지명 비어있는 케이스")
journal_type = refs[refs["유형"] == "학술지(정기간행물)"]
empty_journal = journal_type[journal_type["학술지_원본"].fillna("").str.strip() == ""]
print(f"  학술지 type 총: {len(journal_type)}, 학술지명 비어있음: {len(empty_journal)}")
if len(empty_journal) > 0:
    print("  샘플 (원본 텍스트):")
    for t in empty_journal["원본_텍스트"].head(5):
        print(f"      {t}")

sub("F-3. 연도 추출 실패")
no_year = refs[refs["연도"].isna()]
print(f"  연도 추출 실패: {len(no_year)} / {len(refs)}")
print(f"  유형별: {no_year['유형'].value_counts().to_dict()}")

sub("F-4. 인용 학술지명 — 정규화 미해상도 TOP 20")
from ksip.normalize import add_canonical_column
journal_refs = refs[refs["학술지_원본"].fillna("") != ""]
norm = add_canonical_column(journal_refs, "학술지_원본", "journals", out_col="cid")
unresolved = norm[norm["cid"].isna()]["학술지_원본"].value_counts().head(20)
print(f"  미해상도 unique 학술지: {norm[norm['cid'].isna()]['학술지_원본'].nunique()}")
print(f"  TOP 20:")
for j, n in unresolved.items():
    print(f"      {n:>3} · {j}")

sub("F-5. 인용 저자명 — 자주 등장하는 패턴")
# 학술지/학위/학술대회/보고서 type만 (저자가 분명히 추출되는 경우)
auth_refs = refs[refs["유형"].isin(["학술지(정기간행물)", "학위논문", "학술대회논문", "단행본", "보고서"])]
top_cited_auth = auth_refs[auth_refs["저자_원본"].fillna("") != ""]["저자_원본"].value_counts().head(20)
print("  TOP 20 인용 저자(원본 표기):")
for a, n in top_cited_auth.items():
    print(f"      {n:>3} · {a}")
