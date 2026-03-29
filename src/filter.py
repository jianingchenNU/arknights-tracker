"""
filter.py — 使用 OpenAI gpt-4o-mini 对公告进行相关性过滤和摘要生成
"""

import json
import logging
import os

from openai import OpenAI

SYSTEM_PROMPT = """你是一个游戏公告分类助手。
判断以下公告是否应该推送给玩家。

应该推送的内容：版本更新、数值调整、新地图、新角色/武器/装备、游戏内活动、线下活动/展会、联名合作。
不应该推送的内容：周边商品/实体产品、漫画/动画/影视、设备安全提醒（如Nvidia驱动、GPU、第三方app等）。

如果不应推送，返回 {"relevant": false}。
如果应该推送，返回：
{
  "relevant": true,
  "summary": "详细摘要（见下方要求）",
  "category": "分类名称（见下方规则）"
}

分类规则（按优先级判断，选一个最符合的）：
1. "干员寻访" — 公告主题是干员寻访/招募 banner（如特许寻访、限定寻访、概率提升干员等）
2. "武器申领" — 公告主题是武器申领 banner（标志性词汇：「XX申领」限时特卖、武器概率提升、武库交易所、武库配额等；注意"申领"二字本身即为武器 banner 的专用术语，凡标题含「申领」的公告均属此类）
3. "版本更新" — 公告主题是游戏版本更新/维护（即使同时提及新干员、新武器或新活动，只要核心是版本更新，就归为此类）
4. "活动" — 其他所有应推送内容，包括：游戏内限时活动、线下活动/展会、联名合作、数值调整、新地图等

summary 要求：
- 目标是让玩家读完摘要后无需打开原链接即可了解公告全部关键内容
- 格式根据内容类型自动选择：
  - 结构化信息（如维护时间、奖励数值、版本内容列表）使用要点列表，每点以"• "开头
  - 叙述性内容（如活动说明、联名背景）使用段落
- 必须保留所有具体数字、时间、道具名称、平台信息等关键细节

只返回 JSON，不要有任何其他文字。"""


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 未设置")
    return OpenAI(api_key=api_key)


def filter_and_summarize(announcement: dict) -> dict:
    """
    对单条公告调用 GPT-4o-mini 判断相关性并生成摘要。
    返回:
        {"relevant": False}
        或
        {"relevant": True, "summary": "...", "category": "..."}
    出错时返回 {"relevant": False, "error": "..."} 并记录日志，不中断主流程。
    """
    title = announcement.get("title", "")
    content = announcement.get("content", "")

    user_message = f"公告标题：{title}\n公告内容：{content}"

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)

        # 校验返回结构
        if "relevant" not in result:
            raise ValueError(f"返回 JSON 缺少 relevant 字段: {raw}")

        if result.get("relevant"):
            if "summary" not in result or "category" not in result:
                raise ValueError(f"relevant=true 但缺少 summary/category: {raw}")

        logging.info(
            f"[filter] 公告 {announcement.get('id')} "
            f"relevant={result.get('relevant')} "
            f"category={result.get('category', 'N/A')}"
        )
        return result

    except Exception as e:
        logging.error(
            f"[filter] 公告 {announcement.get('id')} 过滤失败，跳过: {e}"
        )
        return {"relevant": False, "error": str(e)}
