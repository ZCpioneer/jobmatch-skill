#!/usr/bin/env python3
"""Thin client for the JobMatch server. No third-party dependencies."""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

DEFAULT_URL = os.getenv("JOBMATCH_API_URL", "https://zcpionner.cloud/api").rstrip("/")
API_KEY = os.getenv("JOBMATCH_API_KEY", "")
USER_AGENT = "jobmatch-skill/0.5"
BILLING_URL = "https://zcpionner.cloud/account/billing?sku=credits_10"


def _headers() -> dict:
    headers = {"User-Agent": USER_AGENT}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


def _post_json(url: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={**_headers(), "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url: str, timeout: int) -> dict:
    req = urllib.request.Request(url, headers=_headers(), method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_file(
    url: str,
    file_path: Path,
    city: str = "",
    limit: int = 5,
    timeout: int = 90,
) -> dict:
    boundary = "----jobmatch" + uuid.uuid4().hex
    suffix = file_path.suffix.lower() or ".bin"
    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    chunks: list[bytes] = []

    def field(name: str, value: str) -> None:
        chunks.append(
            f"--{boundary}\r\n".encode()
            + f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            + value.encode("utf-8")
            + b"\r\n"
        )

    if city:
        field("city", city)
    field("limit", str(limit))
    chunks.append(
        f"--{boundary}\r\n".encode()
        + f'Content-Disposition: form-data; name="file"; filename="resume{suffix}"\r\n'.encode()
        + f"Content-Type: {mime}\r\n\r\n".encode()
        + file_path.read_bytes()
        + b"\r\n"
    )
    chunks.append(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        url,
        data=b"".join(chunks),
        headers={
            **_headers(),
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(sum(len(c) for c in chunks)),
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _print_me(data: dict) -> None:
    limit = data.get("free_matches_limit", 0)
    used = data.get("free_matches_used", 0)
    remaining = data.get("free_matches_remaining", 0)
    print(f"免费匹配：{used} / {limit} 次（剩余 {remaining}）")
    print(f"Credit 余额：{data.get('credit_balance', 0)}")
    print(
        f"完整匹配：{data.get('match_cost', 1)} credit；"
        f"快速匹配：{data.get('quick_match_cost', 0.1)} credit；"
        f"报告：{data.get('report_cost', 9)} credits"
    )
    packs = data.get("packs") or []
    if packs:
        print("可买：" + "；".join(f"{p['label']} {p['credits']} credits" for p in packs))
    print(f"额度页：{BILLING_URL}")


def _place(match: dict) -> str:
    """Which city to print: the one that matched, else the posting's list."""
    cities = match.get("cities") or ([match["city"]] if match.get("city") else [])
    matched = match.get("city_matched")
    if matched:
        suffix = f"（{len(cities)} 城可选）" if len(cities) > 1 else ""
        return f"｜{matched}{suffix}"
    if cities:
        return f"｜{'、'.join(cities[:3])}"
    return ""


def _print_human(data: dict) -> None:
    matches = data.get("matches") or []
    if not matches:
        print("没有找到匹配岗位。换一份简历或去掉城市限制再试。")
        return
    mode = data.get("mode") or "full"
    label = "快速匹配" if mode == "quick" else "完整匹配"
    print(
        f"找到 {len(matches)} 个匹配岗位（{label}，耗时 {data.get('took_ms', '?')} ms，"
        f"本次 {data.get('cost', 0)} credit）："
    )
    for i, m in enumerate(matches, 1):
        place = _place(m)
        print(f"{i}. {m.get('company', '')}｜{m.get('title', '')}{place}｜{m.get('score', '')}")
        print(f"   {m.get('url', '')}")
        print(f"   {m.get('reason', '')}")


def _print_jobs(data: dict) -> None:
    jobs = data.get("jobs") or []
    dataset = data.get("dataset") or {}
    updated = (dataset.get("updated_at") or "")[:10] or "未知"
    print(f"共 {len(jobs)} 个岗位（数据更新：{updated}，每日同步；搜索免费）：")
    for i, job in enumerate(jobs, 1):
        company = job.get("company_name") or job.get("company") or ""
        city = job.get("city") or job.get("location_raw") or ""
        posted = (job.get("posted_at") or "")[:10]
        print(f"{i}. {company}｜{job.get('title', '')}｜{city}｜{posted}")
        print(f"   {job.get('url', '')}")
    if not jobs:
        print("没有找到岗位；换一个更短的关键词或城市再试。")


def _insufficient_message(body: bytes) -> str:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = {}
    return (
        "额度不足："
        f"当前余额 {payload.get('balance', '?')}，本次需要 {payload.get('cost', '?')}。\n"
        f"到平台获取 credits（价格以网站为准）：{BILLING_URL}"
    )


def _handle_http_error(exc: urllib.error.HTTPError) -> int:
    body = exc.read().decode("utf-8", errors="replace")
    if exc.code == 401:
        print(
            "没有有效的 API Key：到 https://zcpionner.cloud/account/ 登录后创建个人 Key，"
            "放进环境变量 JOBMATCH_API_KEY。不要复用别人的 Key。",
            file=sys.stderr,
        )
        return 1
    if exc.code == 402:
        print(_insufficient_message(body.encode("utf-8")), file=sys.stderr)
        return 1
    if exc.code == 429:
        print("请求过于频繁：等一分钟再试一次，不要连续重试。", file=sys.stderr)
        return 1
    if exc.code in (503, 502, 504):
        print("服务器暂时不可用（本次不扣额度）：稍后重试，仍失败就如实告诉用户。", file=sys.stderr)
        return 1
    print(f"服务器返回 {exc.code}：{body[:400]}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="JobMatch resume -> jobs / job search")
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--file", help="PDF/DOCX/TXT/Markdown resume path")
    source.add_argument("--text", help="resume text instead of a file")
    source.add_argument("--me", action="store_true", help="show free/credit balance and exit")
    source.add_argument("--list", action="store_true", help="search the job pool (no resume)")
    parser.add_argument("--quick", action="store_true", help="vector-only fast match (0.1 credit)")
    parser.add_argument("--q", default="", help="keyword/company for --list")
    parser.add_argument("--city", default="")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--api-url", default=DEFAULT_URL)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    if not args.me and not args.list and not args.file and not args.text:
        parser.error("one of --file, --text, --me or --list is required")
    if args.quick and not (args.file or args.text):
        parser.error("--quick requires --file or --text")
    if args.list:
        args.limit = max(1, min(args.limit, 20))
    elif args.quick:
        args.limit = max(1, min(args.limit, 5))
    else:
        args.limit = max(1, min(args.limit, 10))

    base = args.api_url.rstrip("/")
    try:
        if args.me:
            _print_me(_get_json(f"{base}/v1/me", args.timeout))
            return 0

        if args.list:
            params = {"limit": str(args.limit)}
            if args.q:
                params["q"] = args.q
            if args.city:
                params["city"] = args.city
            url = f"{base}/v1/jobs?{urllib.parse.urlencode(params)}"
            data = _get_json(url, args.timeout)
            if args.json:
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                _print_jobs(data)
            return 0

        if args.file:
            path = Path(args.file).expanduser()
            if not path.is_file():
                print(f"文件不存在：{path}", file=sys.stderr)
                return 2
            endpoint = "/v1/match/quick" if args.quick else "/v1/match"
            data = _post_file(f"{base}{endpoint}", path, args.city, args.limit, args.timeout)
        else:
            payload = {"resume_text": args.text, "limit": args.limit}
            if args.city:
                payload["city"] = args.city
            endpoint = "/v1/match/quick/text" if args.quick else "/v1/match/text"
            data = _post_json(f"{base}{endpoint}", payload, args.timeout)

    except urllib.error.HTTPError as exc:
        return _handle_http_error(exc)
    except urllib.error.URLError as exc:
        print(f"服务器暂不可用：{exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        _print_human(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
