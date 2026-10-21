## 1. 一键启动（推荐，双击即用）

项目根目录有两个**双击就能用**的脚本：

| 脚本 | 作用 |
|---|---|
| **`start.bat`** | **一键启动** Web 界面，自动打开浏览器 |
| **`setup.bat`** | **一键安装依赖**（首次部署/换电脑时用） |

### 首次部署（换电脑/给客户装）
1. 双击 `setup.bat` → 自动创建虚拟环境 + 安装依赖
2. 双击 `start.bat` → 浏览器自动打开 http://localhost:8000

### 日常启动
- 直接双击 `start.bat` 即可
- 关闭黑色窗口 = 停止服务

> 如果你没有 `start.bat`（例如代码是旧版），也可以用下面的手动命令启动。

# 使用指南（中文）

这是 AI 美发店预约助手的完整使用说明。适合**开发者/项目作者**，也适合**交付给客户前的操作**。

## 0. 前置条件（本项目已具备）

- 项目目录：`G:\hair-salon-assistant`
- Python 虚拟环境：`G:\hair-salon-assistant\.venv`（已装好所有依赖）
- 模型配置：`.env` 文件（当前指向 ofm 免费模型网关，零成本）

> ⚠️ **Windows 注意事项**：如果从 Hermes/其他 Python 环境启动，可能会被 `PYTHONPATH` 污染。推荐用下面的 `env -u` 命令启动，确保干净环境。

## 2. 启动 Web 界面（手动方式）

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

## 3. 命令行对话（CLI）

```bash
cd /g/hair-salon-assistant
env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV .venv/Scripts/python.exe main.py
```

输入 `exit` 或 `quit` 退出。

## 4. 配置模型（`.env`）

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


## 4.5 预约信息存储（SQLite，零配置）

预约信息**自动保存到本地 SQLite 数据库**：`G:\hair-salon-assistant\booking.db`。
- 无需配置任何外部服务，预约即落盘
- 每次预约生成一个 `booking_code`（如 `A1B2C3D4`），用于取消/查询
- Google Calendar 是**可选**同步（未配置时，预约仍保存在本地）

### 查看预约列表
```bash
cd /g/hair-salon-assistant
env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV .venv/Scripts/python.exe view_bookings.py
```
输出示例：
```
共 4 条预约（总 4 条）

状态          | 预约时间             | 姓名  | 服务            | 电话          | 预约码
------------+------------------+-----+---------------+-------------+-----
✅ confirmed | 2026-10-22 10:00 | 张伟  | Hair cut      | 13800001111 | A111
❌ cancelled | 2026-10-23 09:00 | 李娜  | Hair wash     | 13700003333 | C333
```

#### 筛选参数

| 参数 | 说明 | 示例 |
|---|---|---|
| `--status confirmed` | 只看已确认 | `view_bookings.py --status confirmed` |
| `--status cancelled` | 只看已取消 | `view_bookings.py --status cancelled` |
| `--search 张` | 按姓名/电话/服务/预约码搜索 | `view_bookings.py --search 张` |
| `--service "Hair cut"` | 按服务名称筛选 | `view_bookings.py --service "Hair cut"` |
| `--code ABC123` | 按预约码查详情 | `view_bookings.py --code ABC123` |
| `--date 2026-10-22` | 按日期筛选 | `view_bookings.py --date 2026-10-22` |
| `--today` | 只看今天 | `view_bookings.py --today` |

> `booking.db` 已被 `.gitignore` 排除（属于运行数据，不入库）。

### 管理者后台（Web 查看预约）
启动服务后，浏览器打开：**http://localhost:8000/bookings**

这是**管理者视图**：显示所有预约统计 + 预约表格（预约码/顾客/电话/服务/时间/状态），数据实时来自 `booking.db`。

> 🔒 **访问保护**：后台受 `ADMIN_TOKEN` 保护。启动前先设置环境变量（如 `set ADMIN_TOKEN=your-token`），然后通过
> `http://localhost:8000/bookings?token=your-token` 访问。未设置 `ADMIN_TOKEN` 时后台返回 503，token 错误返回 401。



## 5. 配置 Google Calendar（可选，用于真实日历同步）

1. 到 Google Cloud Console 创建 OAuth 凭据（桌面应用），下载 `credentials.json`
2. 把文件放到项目 `security/credentials.json`
3. 首次运行会提示授权，生成 `security/token.json`
4. 之后预约会自动写入 Google Calendar

不配置日历也能用（对话功能正常，只是预约不落日历）。

## 6. 运行测试

```bash
cd /g/hair-salon-assistant
env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV .venv/Scripts/python.exe run_tests.py
```

这会**并行**跑：单元测试 + Web 接口测试 + 对话测试，结果写到 `docs/`。

单独跑单元测试：
```bash
env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV .venv/Scripts/python.exe -m pytest -q
```

## 7. 交付给客户（成本转移）

客户不需要碰代码。你要做的：
1. 把项目部署到客户环境（本机 / 免费托管如 Hugging Face Spaces）
2. 在 `.env` 填入**客户自己的** OpenAI/OpenRouter key（客户承担模型 API 费）
3. 让客户打开网页就能用

**你收搭建费，模型成本由客户承担**（详见 README「客户部署与成本转移」）。


### 无模型保底预约（模型限速/不可用时）
当 AI 模型被限速或不可用时，顾客仍可通过**快速预约表单**完成预约（**不调用 AI 模型**）：

- 聊天界面下方有 **"📋 Quick Booking / 快速预约"** 折叠面板
- 填写：姓名 / 电话 / 服务 / 日期 / 时间
- 点击 **Book Now / 立即预约** → 直接写入 `booking.db`，返回 booking code
- 当 AI 回复错误时，前端会自动提示并展开此表单

后端接口：`POST /api/booking`（无模型依赖，生成 booking code + 写入 SQLite）。

## 8. 常见问题

| 问题 | 解决 |
|---|---|
| 启动报 `ModuleNotFoundError: bookinggpt` | 用 `env -u PYTHONPATH ...` 启动，确保在项目根目录 |
| 8000 端口被占用 | 改端口：`--port 8001` |
| AI 回复异常/乱码 | 换一个支持 tool-calling 的标准模型（如 gpt-4o-mini） |
| 日历功能报错 | 检查 `security/credentials.json` 是否存在 |