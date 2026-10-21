# AI Hair Salon Booking Assistant 💇‍♀️🤖

> **本项目基于 [BookingGPT](https://github.com/Hoanganhvu123/BookingGPT)（MIT 许可）二次开发**：
> 将原模型层从 Google Gemini 替换为 **OpenAI 兼容接口**（OpenRouter / 智谱 / 任意 `/v1` 端点），精简依赖并整理为符合 GitHub 规范的维护结构。

## 🌟 Key Features

- 🤖 AI 对话式预约助手（订位 / 查时段 / 取消）
- 📅 Google Calendar 集成（预约自动写入日历）
- 💬 自然语言交互，收集姓名 / 电话 / 服务 / 时间
- 🔌 **模型无关**：任何 OpenAI 兼容 API 均可驱动（OpenRouter、智谱、DeepSeek、客户自带 key）

## 🛠️ Tech Stack

- Python 3.11+
- LangChain（Agent + Tool Calling）
- **OpenAI 兼容模型层**（可替换）
- Google Calendar API

## 🏗️ Project Structure

```
hair-salon-assistant/
├── bookinggpt/
│   ├── agent/            # Agent 与 Prompt 定义
│   │   ├── booking_agent.py
│   │   └── prompt.py
│   ├── tool/             # 工具：创建/查时段/取消预约
│   │   ├── create_event.py
│   │   ├── available_event.py
│   │   └── cancel_event.py
│   ├── __init__.py
│   └── utils.py
├── security/            # Google Calendar 凭据（.example）
├── tests/               # 单元测试
├── main.py              # CLI 入口
├── requirements.txt   # 核心依赖
├── README.md
├── LICENSE             # MIT（原作者许可）
└── .gitignore
```

## 🚀 安装与运行

### 1. 克隆与安装依赖
```bash
git clone <your-fork-url> hair-salon-assistant
cd hair-salon-assistant
pip install -r requirements.txt
```

### 2. 配置环境变量（`.env`）
```bash
# 模型（OpenAI 兼容）
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openrouter.ai/api/v1   # 或智谱/DeepSeek/其他
MODEL_NAME=gpt-4o-mini                            # 按你的模型改

# Google Calendar（可选，用于写日历）
GOOGLE_API_KEY=your_google_api_key_here
```
将 `security/credentials.json.example` 复制为 `security/credentials.json` 并填入 OAuth 凭据（如需 Google Calendar 集成）。

### 3. 运行
```bash
python main.py
```

## 🧪 测试
```bash
pytest
```

## 📄 许可
MIT License（保留原作者 [Hoanganhvu123/BookingGPT](https://github.com/Hoanganhvu123/BookingGPT) 版权）。

## 📌 二次开发待办
- [ ] 用 OpenRouter/智谱实际跑通一次对话
- [ ] 增加 Web/API 界面（FastAPI）便于客户使用
- [ ] 增加 SQLite 备选存储（不依赖 Google Calendar）


## 💰 客户部署与成本转移（OpenAI 标准形式）

本项目模型层使用 **OpenAI 标准兼容接口**（`/v1/chat/completions`），因此**模型 API 成本可以完全转移给客户**：

### 交付给客户的步骤
1. 客户注册任一 OpenAI 兼容服务商并获取 API key（任选其一）：
   - **OpenAI**：https://platform.openai.com/api-keys
   - **OpenRouter**：https://openrouter.ai/keys （聚合多家模型，免绑卡可用免费模型）
   - **DeepSeek / 智谱 / Moonshot** 等国内服务商
2. 在客户的服务器/环境创建 `.env`：
   ```bash
   OPENAI_API_KEY=<客户自己的 key>
   OPENAI_BASE_URL=https://api.openrouter.ai/api/v1   # 按客户选择的服务商
   MODEL_NAME=gpt-4o-mini                             # 按客户选择的模型
   ```
3. 运行 `python main.py` → 所有 AI 调用走客户账户，**API 费用由客户承担**。

### 你的角色
- 你负责**搭建 + 配置 + 交付**，收一次性搭建费（$150-600）和可选月维护费。
- 不承担模型 API 持续成本（客户自付 key 用量）。
- 如需 Google Calendar 集成，同样用客户的 Google 账号 OAuth。

> 这样你不需要维护任何模型服务器/API 额度，真正的"零成本交付"。



## 🌐 Web 界面（作品集 / Gig 演示）

本项目带一个**面向小白客户的聊天 Web 界面**（FastAPI + 前端）：
- **默认英文**，支持 **English / 中文 / Español** 一键切换
- 对话式预约：客户像用微信一样打字，AI 自动回复、查时段、预约
- 零配置：打开网页就能用

### 演示截图（真实浏览器截图）

![English chat — Daisy Salon](docs/screenshots/real-en.png)
![Booking flow in chat](docs/screenshots/real-booking.png)
![Chinese interface](docs/screenshots/real-zh.png)
![Spanish interface](docs/screenshots/real-es.png)
![Quick Booking — no-AI fallback](docs/screenshots/real-quickbook.png)
![Admin dashboard](docs/screenshots/real-admin-db.png)

> 更多截图（预约确认 / 取消 / AI 降级保底）见 `docs/screenshots/`。

- **无 AI 保底预约**：模型限速或不可用时，页面自动展开「快速预约」表单，`POST /api/booking` 直接写入 SQLite（不调用模型）。
- **管理后台**：`http://localhost:8000/bookings`，需设置环境变量 `ADMIN_TOKEN` 后以 `?token=<值>` 访问。

### 运行 Web 界面
```bash
pip install -r requirements.txt
# 配置 .env（模型 key）
.venv/Scripts/python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
# 浏览器打开 http://localhost:8000
```

## 🎯 项目定位
- **作品集**：展示 AI Agent 搭建能力（LangChain + 工具调用 + Web 界面）
- **Fiverr Gig 演示**：接"AI 预约助手 / AI Chatbot"单时，直接演示这个成品
- **GitHub 开源**：可二次开发，MIT 许可

## ✅ 验证记录（2026-10-21）

- **环境**：Python 3.12 venv，依赖已安装
- **模型**：ofm 本地免费网关（OpenAI 兼容 `http://127.0.0.1:18900/v1`，模型 `kilo-auto/free`）
- **结果**：AI 预约助手可正常对话——能列出服务清单、引导客户提供预约信息、调用工具订位/查时段/取消
- **单元测试**：`pytest` 全部通过
- **注意**：交付客户时，将 `.env` 的 `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `MODEL_NAME` 换成客户自己的 OpenAI/OpenRouter key 即可（成本转嫁客户）

### 现场对话验证
```bash
.venv/Scripts/python.exe examples/live_test.py
```
