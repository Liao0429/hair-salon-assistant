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
