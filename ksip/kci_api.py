"""KCI Open API 클라이언트.

엔드포인트: https://open.kci.go.kr/po/openapi/openApiSearch.kci
인증: URL query param `key=...`
응답: XML (UTF-8)

스트리밍 앱(Streamlit) 측에서는 호출하지 않는다 — `scripts/`의 빌드 단계에서만
호출하고 결과를 `data/processed/`의 parquet에 저장. (stlite 정적 배포 호환)
"""
from __future__ import annotations

import hashlib
import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parent.parent
KEY_FILE = ROOT / "KCI_OpenAPI_Key.txt"
CACHE_DIR = ROOT / "data" / "cache"
ENDPOINT = "https://open.kci.go.kr/po/openapi/openApiSearch.kci"
USER_AGENT = "KSIP-DH-research/0.1 (mailto:naspatterns@gmail.com)"

# 정중한 호출 간격 (초). KCI는 명시적 rate limit 없으나 ~2 req/s 안전.
MIN_CALL_INTERVAL = 0.5
# 재시도 횟수 + exponential backoff 베이스(초).
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 1.0
HTTP_TIMEOUT = 30.0

log = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────
# 키 로딩
# ────────────────────────────────────────────────────────────
def load_api_key() -> str:
    """KCI_OpenAPI_Key.txt에서 키 읽기.

    사용자가 KCI 페이지에서 라벨까지 통째로 복사한 케이스를 자동 처리:
    'KCI OpenAPI Key: 61491951' → '61491951'
    """
    if not KEY_FILE.exists():
        raise RuntimeError(
            f"KCI API 키 파일이 없습니다: {KEY_FILE}\n"
            f"https://www.kci.go.kr 마이페이지에서 발급받아 평문으로 저장."
        )
    raw = KEY_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        raise RuntimeError(f"{KEY_FILE} 가 비어있습니다.")
    # 라벨 prefix 자동 제거 (대소문자 무관)
    if ":" in raw:
        prefix, _, value = raw.partition(":")
        # 'KCI OpenAPI Key' 또는 'key' 등이 prefix면 값만 사용
        if "key" in prefix.lower():
            raw = value.strip()
    return raw


# ────────────────────────────────────────────────────────────
# 캐시
# ────────────────────────────────────────────────────────────
def _cache_path(api_code: str, params: dict[str, Any]) -> Path:
    """캐시 파일 경로 — apiCode 단위 폴더 + params 해시."""
    # 키는 캐시 키에서 제외 (보안 + 키 변경 시에도 캐시 유효)
    relevant = {k: v for k, v in sorted(params.items()) if k != "key"}
    payload = urlencode(relevant, doseq=True)
    h = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
    folder = CACHE_DIR / api_code
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{h}.xml"


# ────────────────────────────────────────────────────────────
# Rate limiter (단순한 last-call 추적)
# ────────────────────────────────────────────────────────────
_last_call_at: float = 0.0


def _wait_for_rate_limit() -> None:
    global _last_call_at
    now = time.monotonic()
    elapsed = now - _last_call_at
    if elapsed < MIN_CALL_INTERVAL:
        time.sleep(MIN_CALL_INTERVAL - elapsed)
    _last_call_at = time.monotonic()


# ────────────────────────────────────────────────────────────
# 호출
# ────────────────────────────────────────────────────────────
@dataclass
class APIResponse:
    api_code: str
    params: dict[str, Any]
    raw_xml: str
    from_cache: bool

    @property
    def root(self) -> ET.Element:
        return ET.fromstring(self.raw_xml)


def call(
    api_code: str,
    *,
    use_cache: bool = True,
    **params: Any,
) -> APIResponse:
    """KCI Open API 호출. 캐시 우선, 실패 시 재시도.

    Args:
        api_code: 'articleDetail', 'referenceSearch', 'citationDetail', etc.
        use_cache: True 면 캐시된 응답 사용. False 면 강제 재호출.
        **params: 엔드포인트별 파라미터 (id, sereId, etc.). 'key'는 자동 추가됨.

    Returns:
        APIResponse — raw_xml + parsed root 접근.
    """
    cache_path = _cache_path(api_code, params)
    if use_cache and cache_path.exists():
        return APIResponse(
            api_code=api_code,
            params=params,
            raw_xml=cache_path.read_text(encoding="utf-8"),
            from_cache=True,
        )

    full_params = {"apiCode": api_code, "key": load_api_key(), **params}
    last_err: Exception | None = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        _wait_for_rate_limit()
        try:
            r = requests.get(
                ENDPOINT,
                params=full_params,
                headers={"User-Agent": USER_AGENT},
                timeout=HTTP_TIMEOUT,
            )
            r.raise_for_status()
            r.encoding = "utf-8"
            xml = r.text
            # XML 파싱 시도 (응답 무결성 검증)
            ET.fromstring(xml)
            cache_path.write_text(xml, encoding="utf-8")
            return APIResponse(
                api_code=api_code, params=params, raw_xml=xml, from_cache=False,
            )
        except (requests.RequestException, ET.ParseError) as e:
            last_err = e
            if attempt < RETRY_ATTEMPTS:
                wait = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                log.warning(
                    f"KCI API call failed (attempt {attempt}/{RETRY_ATTEMPTS}): "
                    f"{e!r}. retrying in {wait:.1f}s",
                )
                time.sleep(wait)
            else:
                log.error(f"KCI API call failed permanently: {e!r}")
                raise
    assert last_err is not None
    raise last_err


# ────────────────────────────────────────────────────────────
# 편의 helper
# ────────────────────────────────────────────────────────────
def get_article_detail(arti_id: str, **kw: Any) -> APIResponse:
    return call("articleDetail", id=arti_id, **kw)


def get_reference_search(arti_id: str, **kw: Any) -> APIResponse:
    return call("referenceSearch", id=arti_id, **kw)


def get_citation_detail(sere_id: str, **kw: Any) -> APIResponse:
    return call("citationDetail", id=sere_id, **kw)


def get_article_search(**criteria: Any) -> APIResponse:
    return call("articleSearch", **criteria)


# ────────────────────────────────────────────────────────────
# XML helper
# ────────────────────────────────────────────────────────────
def text_of(element: ET.Element | None) -> str:
    """ElementTree element의 .text 안전 추출."""
    if element is None:
        return ""
    return (element.text or "").strip()


def find_text(parent: ET.Element, path: str) -> str:
    return text_of(parent.find(path))
