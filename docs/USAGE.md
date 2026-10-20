# 使用指南（中文）

这是 AI 美发店预约助手的完整使用说明。适合**开发者/项目作者**，也适合**交付给客户前的操作**。

## 0. 前置条件（本项目已具备）

- 项目目录：`G:\hair-salon-assistant`
- Python 虚拟环境：`G:\hair-salon-assistant\.venv`（已装好所有依赖）
- 模型配置：`.env` 文件（当前指向 ofm 免费模型网关，零成本）

> ⚠️ **Windows 注意事项**：如果从 Hermes/其他 Python 环境启动，可能会被 `PYTHONPATH` 污染。推荐用下面的 `env -u` 命令启动，确保干净环境。

## 1. 启动 Web 界面（最直观，推荐）

```bash
cd /g/hair-salon-assistant
env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV .venv/Scripts/python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

然后浏览器打开：**http://localhost:8000**

你会看到：
- 美发店聊天界面（默认英文）
- 右上角可切换 **English / 中文 / Español**
- 在输入框打字，AI 会帮你预约、查时段、取消

示例对话：
```
顾客: What services do you offer?
AI: 列出服务清单...
顾客: Book a haircut tomorrow at 10am, my name is Liao
AI: 收集信息、确认、预约...
```

停止服务：按 `Ctrl+C`。

## 2. 命令行对话（CLI）

```bash
cd /g/hair-salon-assistant
env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV .venv/Scripts/python.exe main.py
```

输入 `exit` 或 `quit` 退出。

## 3. 配置模型（`.env`）

打开 `.env`，改这三个变量即可换模型（**模型成本可转嫁客户**）：

```bash
OPENAI_API_KEY=客户或你的key
OPENAI_BASE_URL=https://api.openai.com/v1      # 或 OpenRouter/智谱/DeepSeek 等
MODEL_NAME=gpt-4o-mini                          # 按服务商模型名填
```

当前 `.env` 指向 ofm 免费网关（本地，零成本测试用）：
```bash
OPENAI_BASE_URL=http://127.0.0.1:18900/v1
MODEL_NAME=kilo-auto/free
```

## 4. 配置 Google Calendar（可选，用于真实日历同步）

1. 到 Google Cloud Console 创建 OAuth 凭据（桌面应用），下载 `credentials.json`
2. 把文件放到项目 `security/credentials.json`
3. 首次运行会提示授权，生成 `security/token.json`
4. 之后预约会自动写入 Google Calendar

不配置日历也能用（对话功能正常，只是预约不落日历）。

## 5. 运行测试

```bash
cd /g/hair-salon-assistant
env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV .venv/Scripts/python.exe run_tests.py
```

这会**并行**跑：单元测试 + Web 接口测试 + 对话测试，结果写到 `docs/`。

单独跑单元测试：
```bash
env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV .venv/Scripts/python.exe -m pytest -q
```

## 6. 交付给客户（成本转移）

客户不需要碰代码。你要做的：
1. 把项目部署到客户环境（本机 / 免费托管如 Hugging Face Spaces）
2. 在 `.env` 填入**客户自己的** OpenAI/OpenRouter key（客户承担模型 API 费）
3. 让客户打开网页就能用

**你收搭建费，模型成本由客户承担**（详见 README「客户部署与成本转移」）。

## 7. 常见问题

| 问题 | 解决 |
|---|---|
| 启动报 `ModuleNotFoundError: bookinggpt` | 用 `env -u PYTHONPATH ...` 启动，确保在项目根目录 |
| 8000 端口被占用 | 改端口：`--port 8001` |
| AI 回复异常/乱码 | 换一个支持 tool-calling 的标准模型（如 gpt-4o-mini） |
| 日历功能报错 | 检查 `security/credentials.json` 是否存在 |