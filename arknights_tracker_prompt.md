# Claude Code Vibe Coding Prompt
# 明日方舟终末地 公告追踪机器人

---

## 你的任务

你是一个全栈开发专家。请帮我从零开始构建一个**明日方舟：终末地游戏公告自动追踪系统**。
我完全不熟悉这个流程，请一步步引导我，遇到需要我提供信息的地方（比如填入密钥）请明确告诉我该怎么做。

---

## 项目需求

### 功能目标
- 自动抓取《明日方舟：终末地》官方网站的公告页内容
- 使用 AI 过滤，**只保留与游戏内容相关的公告**
- 每天定时自动运行一次（UTC 时间 12:00，即北京时间 20:00）
- 发现新公告后，自动将摘要推送到我的 Discord 频道

### 需要抓取的内容（推送）
- 版本更新 / 新内容上线通知
- 数值调整 / 平衡性改动
- 新地图 / 新关卡上线
- 新角色 / 武器 / 装备介绍
- 游戏内活动公告
- 线下活动 / 展会信息
- 联名合作信息

### 需要过滤掉的内容（不推送）
- 周边商品 / 实体产品
- 漫画 / 动画 / 影视相关
- 设备安全提醒（如 Nvidia 驱动、GPU 相关、第三方 app 公告等）

---

## 技术栈要求

| 模块 | 技术选择 |
|------|----------|
| 运行环境 | GitHub Actions（免费定时任务） |
| 编程语言 | Python 3.11 |
| 网页抓取 | requests + BeautifulSoup4 |
| AI 过滤与总结 | OpenAI API（gpt-4o-mini，便宜高效） |
| 状态存储 | JSON 文件 + Git commit（无需数据库） |
| 通知推送 | Discord Webhook |
| 依赖管理 | requirements.txt |

---

## 项目结构

请按照以下结构创建所有文件：

```
arknights-tracker/
├── .github/
│   └── workflows/
│       └── tracker.yml        # GitHub Actions 定时任务配置
├── src/
│   ├── fetcher.py             # 抓取官网公告
│   ├── filter.py              # 用 Claude API 过滤和总结公告
│   ├── notifier.py            # 发送 Discord 通知
│   └── storage.py             # 管理已推送公告的状态（防重复）
├── data/
│   └── seen_announcements.json  # 记录已处理的公告 ID（初始为空列表）
├── main.py                    # 主入口，串联所有模块
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量示例（不含真实密钥）
└── README.md                  # 使用说明
```

---

## 各模块详细要求

### 1. fetcher.py — 公告抓取

- 目标网站：请先用 requests 访问 `https://wiki.biligame.com/aec/` 或搜索明日方舟终末地官方公告页，找到正确的公告列表 URL
- 如果官网有反爬机制，改用 Playwright 做无头浏览器抓取
- 抓取内容：公告标题、发布时间、公告链接、公告正文摘要
- 返回格式：List of dict，每个 dict 包含 `id`、`title`、`url`、`date`、`content`

### 2. filter.py — AI 过滤与总结

- 使用 OpenAI Python SDK 调用 OpenAI API
- 模型：`gpt-4o-mini`（速度快、成本低）
- 对每条公告发送如下 prompt 进行判断：

```
你是一个游戏公告分类助手。
判断以下公告是否应该推送给玩家。

应该推送的内容：版本更新、数值调整、新地图、新角色/武器/装备、游戏内活动、线下活动/展会、联名合作。
不应该推送的内容：周边商品/实体产品、漫画/动画/影视、设备安全提醒（如Nvidia驱动、GPU、第三方app等）。

如果不应推送，返回 {"relevant": false}。
如果应该推送，返回：
{
  "relevant": true,
  "summary": "总结公告核心内容",
  "category": "版本更新|数值调整|新地图|新角色|活动|线下活动|联名合作"
}
公告标题：{title}
公告内容：{content}
```

- 确保返回合法 JSON，做好异常处理

### 3. storage.py — 状态管理

- 读写 `data/seen_announcements.json`
- 提供两个函数：
  - `is_seen(announcement_id)` → bool
  - `mark_as_seen(announcement_id)`
- 防止同一条公告被重复推送

### 4. notifier.py — Discord 推送

- 使用 Discord Webhook（通过环境变量 `DISCORD_WEBHOOK_URL` 读取）
- 每条公告发送一个 Discord Embed，包含：
  - 标题（加粗，带链接）
  - 分类标签（用 emoji 区分：🔄版本更新 ⚖️数值调整 🗺️新地图 👤新角色 🎮活动 📍线下活动 🤝联名合作）
  - AI 总结内容
  - 发布时间
  - 颜色：蓝色 (0x3498db)
- 如果当天没有新公告，不发送任何消息（静默）

### 5. main.py — 主流程

```python
# 伪代码逻辑，请实现完整版
announcements = fetch_announcements()
new_ones = [a for a in announcements if not is_seen(a['id'])]
for ann in new_ones:
    result = filter_and_summarize(ann)
    if result['relevant']:
        send_to_discord(ann, result)
    mark_as_seen(ann['id'])
```

### 6. tracker.yml — GitHub Actions

```yaml
# 要求：
# - 触发方式：schedule cron = '0 12 * * *'（每天 UTC 12:00）
# - 同时支持手动触发（workflow_dispatch）
# - 环境变量从 GitHub Secrets 读取：
#     OPENAI_API_KEY
#     DISCORD_WEBHOOK_URL
# - 运行后如果 seen_announcements.json 有变化，自动 git commit 并 push
#   commit message: "chore: update seen announcements [skip ci]"
```

### 7. README.md — 使用说明

请用中文写一份清晰的使用说明，包含：
1. 项目介绍
2. 前置准备（需要哪些账号和密钥）
3. 一步步的部署教程（Fork 仓库 → 设置 Secrets → 启用 Actions）
4. 如何手动触发一次测试
5. 如何修改检查时间

---

## 密钥管理

项目需要以下两个密钥，采用**本地文件 + GitHub Secrets 双模式**：

### 本地运行
项目根目录创建了`apikey.txt`：

```
OPENAI_API_KEY=你的OpenAI API密钥
DISCORD_WEBHOOK_URL=你的Discord Webhook地址
```

代码读取逻辑如下，请严格按此实现：

```python
import os

def load_keys():
    """本地从 apikey.txt 读取，GitHub Actions 从环境变量读取"""
    if os.path.exists("apikey.txt"):
        with open("apikey.txt") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
```

在 `main.py` 最开头调用 `load_keys()`，之后所有模块统一用 `os.environ.get("OPENAI_API_KEY")` 读取。

### GitHub Actions 运行
从 GitHub Secrets 读取（变量名相同），无需 `apikey.txt`。

### 安全设置（重要）
在 `.gitignore` 中加入以下内容，确保 `apikey.txt` **绝对不会**被上传到 GitHub：

```
apikey.txt
```

---

## 错误处理要求

- 网络请求失败：重试3次，每次间隔5秒
- OpenAI API 调用失败：记录错误日志，跳过该条公告，不中断整体流程
- Discord 推送失败：打印错误信息，不中断流程
- 整体运行失败：GitHub Actions 标记为失败，方便我排查

---

## 开始执行

请按以下顺序执行：

1. 首先访问明日方舟终末地官方公告页，确认正确的 URL 和页面结构。URL: https://endfield.hypergryph.com/news
2. 创建完整的项目目录和所有文件
3. 在每个关键步骤后告诉我：**"下一步你需要做什么"**（比如获取密钥、创建 GitHub 仓库等）
4. 所有代码写完后，给我一份清单，列出我需要手动操作的所有步骤

开始吧！
