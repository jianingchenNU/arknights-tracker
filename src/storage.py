"""
storage.py — 管理已推送公告的状态，防止重复推送
数据存储在 data/seen_announcements.json
"""

import json
import logging
import os

DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "seen_announcements.json",
)

_seen_ids: set = None  # 运行期间的内存缓存


def _load() -> set:
    global _seen_ids
    if _seen_ids is not None:
        return _seen_ids

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            _seen_ids = set(data) if isinstance(data, list) else set()
        except Exception as e:
            logging.warning(f"[storage] 读取 {DATA_FILE} 失败，重置为空: {e}")
            _seen_ids = set()
    else:
        _seen_ids = set()

    return _seen_ids


def _save() -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(_seen_ids), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"[storage] 写入 {DATA_FILE} 失败: {e}")


def is_seen(announcement_id: str) -> bool:
    """返回该公告是否已经处理过。"""
    return str(announcement_id) in _load()


def mark_as_seen(announcement_id: str) -> None:
    """将公告标记为已处理并持久化。"""
    ids = _load()
    ids.add(str(announcement_id))
    _save()
    logging.debug(f"[storage] 已标记: {announcement_id}")
