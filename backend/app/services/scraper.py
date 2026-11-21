"""사용자가 입력한 URL의 환불 안내 페이지를 가져온다.

서버가 사용자 입력 주소로 요청을 보내는 기능이라 SSRF(내부망 접근)를 막는 것이 핵심이다.
- http/https, 기본 포트(80/443)만 허용
- 호스트가 가리키는 IP가 공인 주소가 아니면 거부 (localhost, 사설망, 클라우드 메타데이터 등)
- 리다이렉트는 직접 따라가며 매번 같은 검사를 한다
- robots.txt 준수, 응답 크기·타임아웃 제한, 로그인이 필요한 페이지는 수집하지 않음
"""

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "RefundStationBot/0.1"
MAX_BYTES = 2_000_000
MAX_TEXT_CHARS = 12_000
MAX_REDIRECTS = 3
ALLOWED_PORTS = {None, 80, 443}


class ScrapeError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class ScrapedPage:
    final_url: str
    text: str


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return (not ip.is_global) or ip.is_multicast


def validate_public_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ScrapeError("INVALID_URL", "http:// 또는 https:// 로 시작하는 주소를 입력해 주세요.")
    if parsed.username or parsed.password:
        raise ScrapeError("INVALID_URL", "계정 정보가 들어간 주소는 사용할 수 없습니다.")
    try:
        port = parsed.port
    except ValueError:
        raise ScrapeError("INVALID_URL", "주소의 포트 번호가 올바르지 않습니다.")
    if port not in ALLOWED_PORTS:
        raise ScrapeError("URL_NOT_ALLOWED", "접근할 수 없는 주소입니다.")
    try:
        infos = socket.getaddrinfo(
            parsed.hostname, port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM
        )
    except socket.gaierror:
        raise ScrapeError("HOST_NOT_FOUND", "주소를 찾을 수 없습니다. URL을 다시 확인해 주세요.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if _is_blocked_ip(ip):
            raise ScrapeError("URL_NOT_ALLOWED", "접근할 수 없는 주소입니다.")
    return url


def html_to_text(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript", "template", "svg"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    return text[:MAX_TEXT_CHARS]


def _read_limited(response: httpx.Response, limit: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_bytes():
        total += len(chunk)
        if total > limit:
            chunks.append(chunk[: len(chunk) - (total - limit)])
            break
        chunks.append(chunk)
    return b"".join(chunks)


def _robots_allows(client: httpx.Client, url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        with client.stream("GET", robots_url) as resp:
            if resp.status_code != 200:
                return True
            body = _read_limited(resp, 200_000)
    except httpx.HTTPError:
        return True
    parser = RobotFileParser()
    parser.parse(body.decode("utf-8", errors="replace").splitlines())
    return parser.can_fetch(USER_AGENT, url)


def fetch_page(url: str, timeout: float) -> ScrapedPage:
    current = validate_public_url(url)
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "ko,en;q=0.8"},
        ) as client:
            for _ in range(MAX_REDIRECTS + 1):
                if not _robots_allows(client, current):
                    raise ScrapeError(
                        "ROBOTS_DISALLOWED", "이 사이트는 자동 수집을 허용하지 않습니다. 규정 텍스트를 직접 붙여넣어 주세요."
                    )
                with client.stream("GET", current) as resp:
                    if resp.is_redirect:
                        location = resp.headers.get("location")
                        if not location:
                            raise ScrapeError("FETCH_FAILED", "페이지를 가져오지 못했습니다.")
                        current = validate_public_url(urljoin(current, location))
                        continue
                    if resp.status_code in (401, 403):
                        raise ScrapeError(
                            "ACCESS_DENIED", "로그인이 필요하거나 접근이 차단된 페이지입니다. 규정 텍스트를 직접 붙여넣어 주세요."
                        )
                    if resp.status_code >= 400:
                        raise ScrapeError("FETCH_FAILED", f"페이지를 가져오지 못했습니다. (HTTP {resp.status_code})")
                    content_type = resp.headers.get("content-type", "").lower()
                    if "html" not in content_type and "text/plain" not in content_type:
                        raise ScrapeError("NOT_HTML", "웹 페이지(HTML) 주소가 아닙니다.")
                    body = _read_limited(resp, MAX_BYTES)
                text = html_to_text(body)
                if len(text) < 50:
                    raise ScrapeError(
                        "EMPTY_PAGE",
                        "페이지에서 내용을 읽지 못했습니다. 자바스크립트로 그려지는 페이지일 수 있어요. 규정 텍스트를 직접 붙여넣어 주세요.",
                    )
                return ScrapedPage(final_url=current, text=text)
    except httpx.TimeoutException:
        raise ScrapeError("TIMEOUT", "페이지 응답이 너무 늦어 가져오지 못했습니다.")
    except httpx.HTTPError:
        raise ScrapeError("FETCH_FAILED", "페이지를 가져오지 못했습니다.")
    raise ScrapeError("TOO_MANY_REDIRECTS", "주소가 너무 많이 이동(리다이렉트)합니다.")
