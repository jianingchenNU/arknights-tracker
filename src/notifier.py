"""
notifier.py — 通过 Discord Webhook 推送公告 Embed
"""

import logging
import os

import requests

CATEGORY_EMOJI = {
    "版本更新": "🔄",
    "干员寻访": "👤",
    "武器申领": "⚔️",
    "活动": "🎮",
}

EMBED_COLOR = 0x3498DB  # 蓝色


def send_to_discord(announcement: dict, filter_result: dict) -> None:
    """
    发送单条公告到 Discord Webhook。
    announcement: fetcher 返回的公告 dict
    filter_result: filter_and_summarize 返回的结果 dict
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logging.error("[notifier] DISCORD_WEBHOOK_URL 未设置，跳过推送")
        return

    category = filter_result.get("category", "")
    emoji = CATEGORY_EMOJI.get(category, "📢")
    summary = filter_result.get("summary", "（无摘要）")
    title = announcement.get("title", "（无标题）")
    url = announcement.get("url", "")
    date = announcement.get("date", "")

    embed = {
        "title": f"{emoji} {title}",
        "url": url,
        "description": summary,
        "color": EMBED_COLOR,
        "fields": [
            {"name": "分类", "value": f"`{category}`" if category else "`未分类`", "inline": True},
            {"name": "发布时间", "value": date or "未知", "inline": True},
        ],
        "footer": {"text": "明日方舟：终末地 公告追踪"},
    }

    payload = {"embeds": [embed]}

    try:
        resp = requests.post(webhook_url, json=payload, timeout=15)
        resp.raise_for_status()
        logging.info(f"[notifier] 推送成功: {title}")
    except Exception as e:
        logging.error(f"[notifier] 推送失败 ({title}): {e}")
