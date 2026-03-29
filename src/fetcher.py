"""
fetcher.py — 抓取明日方舟:终末地官方公告列表及详情页正文
目标页: https://endfield.hypergryph.com/news
数据嵌入在 Next.js RSC 的初始 HTML 中，无需 Playwright。
"""

import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://endfield.hypergryph.com"
NEWS_LIST_URL = f"{BASE_URL}/news"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_with_retry(url: str, max_retries: int = 3, retry_delay: int = 5) -> Optional[str]:
    """带重试的 HTTP GET，失败3次才放弃。"""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            return resp.text
        except Exception as e:
            logging.warning(f"[fetcher] 第 {attempt + 1} 次请求失败 {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    logging.error(f"[fetcher] 所有 {max_retries} 次请求均失败: {url}")
    return None


def _find_json_array(text: str, key: str) -> Optional[list]:
    """
    在字符串中找到 "key": [...] 并安全地解析出整个 JSON 数组。
    使用括号计数而非正则，避免嵌套结构截断问题。
    """
    search_key = f'"{key}"'
    pos = text.find(search_key)
    if pos == -1:
        return None

    bracket_pos = text.find("[", pos + len(search_key))
    if bracket_pos == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False

    for i in range(bracket_pos, len(text)):
        c = text[i]
        if escape_next:
            escape_next = False
            continue
        if c == "\\" and in_string:
            escape_next = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[bracket_pos : i + 1])
                except json.JSONDecodeError:
                    return None

    return None


def _extract_bulletins(html: str) -> list:
    """
    从 Next.js RSC HTML 中提取 bulletins 数组。
    先在原始 HTML 中直接搜索；若失败，尝试对 _next_f 脚本内容 JSON 解码后再搜索。
    """
    # 策略1：直接在原始 HTML 文本中搜索
    result = _find_json_array(html, "bulletins")
    if result:
        logging.info(f"[fetcher] 策略1 成功，找到 {len(result)} 条公告")
        return result

    # 策略2：提取 self.__next_f.push([1,"..."]) 中的字符串，JSON 解码后再搜索
    pattern = re.compile(r'self\.__next_f\.push\(\s*\[\s*1\s*,\s*"((?:[^"\\]|\\.)*)"\s*\]\s*\)')
    for m in pattern.finditer(html):
        try:
            decoded = json.loads('"' + m.group(1) + '"')
            result = _find_json_array(decoded, "bulletins")
            if result:
                logging.info(f"[fetcher] 策略2 成功，找到 {len(result)} 条公告")
                return result
        except Exception:
            continue

    logging.error("[fetcher] 未能从页面中提取到 bulletins 数据")
    return []


def _extract_content_text(html: str) -> str:
    """
    从详情页 HTML 中提取公告正文，返回纯文本。
    正文位于 class 含 'NoticeDetail_content' 的 div 中，可直接用 BeautifulSoup 定位。
    最多返回 3000 字符供 GPT 使用。
    """
    soup = BeautifulSoup(html, "html.parser")

    # 定位正文容器（class 名含 NoticeDetail_content，带 hash 后缀）
    content_div = soup.find(
        "div", class_=lambda c: c and "NoticeDetail_content" in c
    )
    if content_div:
        text = content_div.get_text(separator="\n", strip=True)
        if len(text) > 50:
            return text[:3000]

    return ""


def fetch_announcement_content(cid: str) -> str:
    """抓取单条公告详情页，返回正文纯文本。失败时返回空字符串。"""
    url = f"{BASE_URL}/news/{cid}"
    html = fetch_with_retry(url)
    if not html:
        logging.warning(f"[fetcher] 详情页请求失败: {url}")
        return ""
    text = _extract_content_text(html)
    if text:
        logging.info(f"[fetcher] 详情页内容抓取成功 (cid={cid}, {len(text)} 字符)")
    else:
        logging.warning(f"[fetcher] 详情页内容提取为空 (cid={cid})")
    return text


def fetch_announcements() -> list:
    """
    抓取公告列表，并对每条公告额外请求详情页获取正文全文。
    每条 dict 包含: id, title, url, date, content, tab
    """
    logging.info(f"[fetcher] 开始抓取公告列表: {NEWS_LIST_URL}")
    html = fetch_with_retry(NEWS_LIST_URL)
    if not html:
        return []

    bulletins = _extract_bulletins(html)
    if not bulletins:
        return []

    announcements = []
    for i, b in enumerate(bulletins):
        cid = str(b.get("cid", "")).strip()
        title = b.get("title", "").strip()
        brief = (b.get("brief") or "").strip()
        display_time = b.get("displayTime", 0)
        tab = b.get("tab", "")

        if not cid or not title:
            continue

        date_str = ""
        if display_time:
            try:
                date_str = datetime.fromtimestamp(
                    int(display_time), tz=timezone.utc
                ).strftime("%Y-%m-%d")
            except Exception:
                pass

        # 抓取详情页正文；失败时退回到 brief 或 title
        logging.info(f"[fetcher] 抓取详情页 ({i+1}/{len(bulletins)}): {title}")
        full_content = fetch_announcement_content(cid)
        content = full_content or brief or title

        announcements.append(
            {
                "id": cid,
                "title": title,
                "url": f"{BASE_URL}/news/{cid}",
                "date": date_str,
                "content": content,
                "tab": tab,
            }
        )

        # 礼貌性延迟，避免对服务器过于频繁请求
        if i < len(bulletins) - 1:
            time.sleep(1)

    logging.info(f"[fetcher] 解析完成，共 {len(announcements)} 条公告")
    return announcements
