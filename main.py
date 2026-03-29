"""
main.py — 主入口，串联所有模块
运行方式:
    python main.py
本地运行时从 apikey.txt 读取密钥；GitHub Actions 从环境变量读取。
"""

import logging
import os
import sys


# ── 密钥加载（必须最先执行）──────────────────────────────────────────────────

def load_keys() -> None:
    """本地从 apikey.txt 读取密钥；GitHub Actions 直接使用环境变量，无需此文件。"""
    if os.path.exists("apikey.txt"):
        with open("apikey.txt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        logging.info("[main] 已从 apikey.txt 加载密钥")


load_keys()


# ── 日志配置 ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,  # 覆盖 openai SDK 等第三方库提前注册的 handler
)


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main() -> None:
    from src.fetcher import fetch_announcements
    from src.filter import filter_and_summarize
    from src.notifier import send_to_discord
    from src.storage import is_seen, mark_as_seen

    logging.info("=== 明日方舟：终末地 公告追踪 开始运行 ===")

    # 1. 抓取公告列表
    announcements = fetch_announcements()
    if not announcements:
        logging.warning("[main] 未获取到任何公告，退出")
        sys.exit(0)

    # 2. 过滤出未处理的新公告
    new_ones = [a for a in announcements if not is_seen(a["id"])]
    logging.info(f"[main] 共 {len(announcements)} 条公告，其中 {len(new_ones)} 条未处理")

    if not new_ones:
        logging.info("[main] 没有新公告，静默退出")
        sys.exit(0)

    # 3. 对每条新公告进行 AI 过滤 + Discord 推送
    pushed = 0
    for ann in new_ones:
        result = filter_and_summarize(ann)

        if result.get("relevant"):
            send_to_discord(ann, result)
            pushed += 1

        # 无论是否推送，都标记为已处理，防止下次重复判断
        mark_as_seen(ann["id"])

    logging.info(f"[main] 本次运行完成，推送 {pushed} 条公告")
    logging.info("=== 运行结束 ===")


if __name__ == "__main__":
    main()
