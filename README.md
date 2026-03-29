# 明日方舟：终末地 公告追踪机器人

自动抓取《明日方舟：终末地》官方公告，用 AI 过滤游戏相关内容，每天定时推送到你的 Discord 频道。

---

## 功能介绍

- 每天 UTC 12:00（北京时间 20:00）自动运行
- 抓取官方公告页所有公告
- 使用 GPT-4o-mini 自动过滤，只推送游戏相关内容（版本更新、活动、新角色等）
- 过滤掉周边商品、漫画/动画、驱动安全提醒等无关内容
- 通过 Discord Embed 推送，含分类 emoji、AI 摘要、发布时间
- 防重复推送，已推送过的公告不会再次发送

---

## 前置准备

需要以下两个密钥：

### 1. OpenAI API Key
1. 前往 [platform.openai.com](https://platform.openai.com)，注册/登录
2. 进入 **API Keys** 页面，点击 **Create new secret key**
3. 复制密钥（格式：`sk-...`）

### 2. Discord Webhook URL
1. 打开 Discord，进入你想推送的频道
2. 点击频道设置 → **整合** → **Webhook** → **新 Webhook**
3. 复制 Webhook URL（格式：`https://discord.com/api/webhooks/...`）

---

## 部署教程

### 第一步：Fork 仓库

1. 打开本项目的 GitHub 页面
2. 点击右上角 **Fork**，将仓库 Fork 到你自己的账号

### 第二步：设置 GitHub Secrets

1. 进入你 Fork 后的仓库页面
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**，分别添加：
   - Name: `OPENAI_API_KEY`，Value: 你的 OpenAI 密钥
   - Name: `DISCORD_WEBHOOK_URL`，Value: 你的 Discord Webhook URL

### 第三步：启用 GitHub Actions

1. 点击仓库页面的 **Actions** 选项卡
2. 如果看到 "Workflows aren't being run on this forked repository" 的提示，点击 **I understand my workflows, go ahead and enable them**
3. 完成！之后每天 UTC 12:00 会自动运行

---

## 手动触发测试

1. 进入仓库 **Actions** 选项卡
2. 左侧列表中点击 **Arknights Endfield Tracker**
3. 右侧点击 **Run workflow** → **Run workflow**
4. 等待约 30 秒，查看运行日志；如有新公告，Discord 会收到消息

---

## 修改检查时间

编辑 `.github/workflows/tracker.yml` 中的 cron 表达式：

```yaml
- cron: "0 12 * * *"
```

格式为 `分 时 日 月 星期`（UTC 时间）。例如：
- `"0 8 * * *"` → 每天 UTC 08:00（北京时间 16:00）
- `"0 0 * * *"` → 每天 UTC 00:00（北京时间 08:00）

---

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 创建密钥文件（参考 .env.example）
cp .env.example apikey.txt
# 编辑 apikey.txt，填入真实密钥

# 运行
python main.py
```

> `apikey.txt` 已被 `.gitignore` 排除，不会上传到 GitHub。

---

## 项目结构

```
├── .github/workflows/tracker.yml   # GitHub Actions 定时任务
├── src/
│   ├── fetcher.py                   # 抓取官网公告
│   ├── filter.py                    # GPT-4o-mini 过滤与摘要
│   ├── notifier.py                  # Discord Webhook 推送
│   └── storage.py                   # 防重复状态管理
├── data/seen_announcements.json     # 已处理公告 ID 记录
├── main.py                          # 主入口
├── requirements.txt
└── .env.example                     # 密钥模板
```
