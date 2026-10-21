# 审计报告：hair-salon-assistant（2026-10-21）

> 审计任务 t_06776de2 产出物。供后续优化（前端 t_60c69427 / 后端 t_6342ab01 / 测试 t_be02b7cb / 开源就绪 t_c0c08527）使用。
> 本次审计只读，未修改任何代码。

## 1. 项目现状概览

- **技术栈**：Python 3.12 venv、LangChain 0.2（Agent + Tool Calling）、OpenAI 兼容模型层、FastAPI + uvicorn + Jinja2、SQLite（booking.db）、Google Calendar API（可选）
- **结构**：`bookinggpt/{agent,tool}` 为核心包；`app.py` Web 入口；`main.py` CLI；`templates/` 前端；`tests/` 单元测试；`docs/` 文档与截图
- **模型配置**：`.env` 指向本地 OFM 免费网关 `http://127.0.0.1:18900/v1`（零成本测试）；交付客户时换客户 key
- **依赖**：17 个 requirements（详见 §5）

## 2. 测试现状（实测）

- `pytest -q` → **13 passed, 0 failed**（2.13s，3 个 deprecation warning）
- 真正含测试的文件：`test_booking_agent.py`(5)、`test_output_parser.py`(5)、`test_tool_output.py`(3) = 13
- **伪测试文件**（0 个 test 函数）：`test_available_event.py`、`test_cancel_event.py`、`test_duplicate_event.py`、`test_create_event.py` —— 是**生产源码的重复副本**，非测试
- `run_tests.py` 并行跑单元 + Web + 对话测试（对话测试真实调用模型），报告写进 docs/

## 3. 发现的问题（按严重度）

### 严重（开源/交付前必须修）

| 编号 | 问题 | 位置 |
|---|---|---|
| **C1** | **`POST /api/booking` 后端缺失**。前端快速预约表单调用它，USAGE.md 也声称存在，但 `app.py` 未实现 → 表单点击必 404，无模型保底预约功能实际不可用。 | `app.py`（无此路由）；`templates/index.html:216`；`docs/USAGE.md:166` |
| **C2** | **预约日期永远被硬编码为“明天”**。`EventInfo` 模型只有 `start_time/end_time`（HH:MM），无日期字段；`create_event()` 用 `current_time + timedelta(days=1)` 拼日期。用户说“这周五 2 点”时，落库/写日历的是“明天 2 点”。 | `bookinggpt/tool/create_event.py:35-42,92-108` |
| **C3** | **`/bookings` 管理后台无任何鉴权**。任何人访问即可查看全部客户姓名/电话/服务/时间（PII）。交付客户或部署到公网时是隐私风险。 | `app.py:73-85` |

### 高

| 编号 | 问题 | 位置 |
|---|---|---|
| H1 | `tests/test_available_event.py`、`test_cancel_event.py`、`test_duplicate_event.py` 是**原版源码副本**，仍含原作者硬编码路径 `E:\chatbot\SaleGPT\security\credentials.json`（即 utils.py 已修复的 H1 老问题），且被 git 跟踪。误导维护者，有安全气味。 | 上述 3 文件 |
| H2 | `tests/test_create_event.py` 是生产 `create_event.py` 的重复副本（未 import 生产模块），测的不是真实代码。 | `tests/test_create_event.py` |
| H3 | **每次对话都重建 AgentExecutor**。`call_agent()` 每次调用 `create_tool_calling_agent()` + `AgentExecutor()`，同一会话重复构建 agent，浪费。 | `bookinggpt/agent/booking_agent.py:25-38` |
| H4 | **`/api/chat` 无速率限制/输入长度限制**。模型成本可被刷爆，公网部署有成本风险。 | `app.py:51-62` |

### 中

| 编号 | 问题 | 位置 |
|---|---|---|
| M1 | 三个工具各自复制一份 `get_credentials()`（DRY 违反），且逻辑完全一致。 | 三个 tool 文件 |
| M2 | 时区硬编码 `Asia/Ho_Chi_Minh`，无法配置（客户可能在中国/其他时区）。 | `create_event.py:174`、`available_event.py:82,107` |
| M3 | `GOOGLE_API_KEY` 环境变量读取后从未使用；`create_event.py` 有多个未使用 import（`create_tool_calling_agent`、`AgentExecutor`、`PROMPT_TEMPLATE`、`ChatPromptTemplate`）。 | `create_event.py:13,19-20,23,28` |
| M4 | `agents` 字典按 session_id 无限增长（内存泄漏，长驻服务会累积）。 | `app.py:36-41` |
| M5 | `cancel_booking()` 不检查受影响行数，`UPDATE` 0 行也返回“已取消”（假成功）。 | `bookinggpt/storage.py:52-66`、`cancel_event.py:55-60` |
| M6 | `README.md:117` 引用 `docs/demo.png`，而该图是早期渲染 mockup（480x800，与真实浏览器截图不符）。 | `README.md`、`docs/demo.png` |
| M7 | `docs/screenshots/screen-*.png`（`screen-admin`、`screen-chat`、`screen-chat-full`、`screen-en`、`screen-zh`）是 headless Chromium 渲染图，正是用户要求删除的“脚本渲染示意图”，但仍被 git 跟踪。 | `docs/screenshots/` |
| M8 | 新真实截图未提交：`real-cancel-confirmed.png`、`real-services-degraded.png` 是 untracked 新文件；`real-booking.png`、`real-booking-confirmed.png`、`real-cancel.png`、`real-services.png` 有未提交修改。 | git status |
| M9 | 缺少真实浏览器截图的 i18n（中文/西语）版本。现有 `screen-en/zh` 是渲染图。 | `docs/screenshots/` |
| M10 | 依赖冗余：`langchain-community`、`python-multipart` 只出现在 requirements.txt，代码从未 import。 | `requirements.txt:6,17` |

### 低

| 编号 | 问题 | 位置 |
|---|---|---|
| L1 | `app.py:70` 重复 import `HTMLResponse`（顶部已导入）。默认 `base_url` 在 `app.py`、`main.py`、`examples/live_test.py` 不一致。 | `app.py:70`、`main.py:20`、`live_test.py:14` |
| L2 | `static/` 目录为空但仍被 `app.mount("/static", ...)` 挂载。 | `app.py:23`、`static/` |
| L3 | 工作区残留 `.env.bak`（已 gitignore，但应删除避免困惑）。 | 根目录 |
| L4 | `security/credentials.json.example`、`security/token.json.example` 是空文件，应放模板内容。 | `security/*.example` |
| L5 | pytest 有 3 个 deprecation warning（Pydantic V1/V2 混用、`.schema()` 已弃用）。 | 测试输出 |

## 4. 优化清单（按子任务分发）

### 4.1 后端优化（t_6342ab01）

1. **新增 `POST /api/booking`**（快速预约保底）：接收 name/phone/service/date/time → 校验必填 → 生成 booking_code → 写 `booking.db` → 返回 `{booking_code}`。（C1）
2. **修复日期硬编码**：给 `EventInfo` 增加 `date: Optional[str]` 字段，`create_event()` 用请求的 date（解析 YYYY-MM-DD），无日期时再回退“明天”；结束时间按服务时长推算。同时更新 extraction prompt。（C2）
3. **`/bookings` 加鉴权**：最简单方案是环境变量 `ADMIN_TOKEN`，访问 `/bookings` 需 `?token=` 或 Cookie 校验；README 注明。（C3）
4. 抽 `bookinggpt/llm.py` 提供 `create_llm()`，统一 main/app/live_test 默认值。（L1）
5. 抽共享 `get_credentials()` 到 `bookinggpt/google_auth.py`，三个工具复用。（M1）
6. `/api/chat` 加基础限流（如每 IP/session 每分钟 N 次）+ message 长度上限。（H4）
7. `cancel_booking()` 返回受影响行数，工具据此报告“未找到匹配预约”而非假成功。（M5）
8. 清理 `create_event.py` 未使用 import 与 `GOOGLE_API_KEY`。（M3）
9. 时区改为 `os.getenv("SALON_TIMEZONE", "Asia/Ho_Chi_Minh")`。（M2）
10. 给 `agents` 加容量上限/清理策略（如 LRU 或 session 空闲超时）。（M4）

### 4.2 前端优化与效果图（t_60c69427）

1. 快速预约表单在 `POST /api/booking` 就绪后即可工作；后端未就绪前前端应给出可读错误。（C1）
2. **删除** `docs/screenshots/screen-*.png`（脚本渲染图，违反用户“真实浏览器截图”要求）。（M7）
3. **替换** `docs/demo.png` 引用：README 改用 `docs/screenshots/real-booking.png` 或新增一张真实首屏截图。（M6）
4. **提交** 新真实截图 `real-cancel-confirmed.png`、`real-services-degraded.png` 及已修改的 4 张 real-* 图。（M8）
5. **补拍** 真实 i18n 截图（中文/西语界面）作为新 `real-zh.png` / `real-es.png`。（M9）
6. 可选：优化移动端/暗色模式、无 JS 时表单不可用的提示等体验细节。

### 4.3 测试补充（t_be02b7cb）

1. **删除 4 个伪测试文件**：`test_available_event.py`、`test_cancel_event.py`、`test_duplicate_event.py`、`test_create_event.py`（它们是源码副本，不是测试）。
2. 用 `unittest.mock` / pytest fixture 重写 `test_create_event`，**import 生产模块** `bookinggpt.tool.create_event.CalendarTool`，mock LLM 返回 + mock Google Calendar service，断言 `create_booking` 被调用、日期正确。
3. 新增 `tests/test_storage.py`：测 `create_booking` / `cancel_booking`（含 rowcount）/ `list_bookings`（筛选、排序、状态过滤）。
4. 新增 `tests/test_api.py`（FastAPI TestClient）：`GET /`、`GET /api/health`、`POST /api/booking`（正常 + 缺字段 400）、`POST /api/chat`（mock agent）、`GET /bookings` 鉴权（401/403）。
5. 新增 `BookingAgent` 端到端测试：用 FakeLLM（返回带 tool_call 的 AIMessage）验证 agent 会调用工具、记忆会保存。
6. 新增“日期处理”测试：给定用户指定日期，断言 `create_event` 不总是明天。
7. 清理 pytest warning（Pydantic V1/V2 混用来自 langchain 旧版，可升级 langchain 或忽略；`.schema()` 警告可改用 `model_json_schema`）。

### 4.4 开源就绪（t_c0c08527）

1. **敏感信息扫描**：已确认 `.env`/`.env.bak`/`booking.db`/`credentials.json`/`token.json` 均被 `.gitignore` 忽略，git 跟踪清单无敏感文件（本次已核验）。无需清理，但应在 README 强调。
2. `security/*.example` 填入模板内容（credentials.json 的字段结构、token 占位说明）。（L4）
3. 删除工作区 `.env.bak`、`*.pyc` 缓存、`static/` 空目录（或放入占位说明）。（L3/L2）
4. README 效果图换成真实截图；补充 `/bookings` 与 `POST /api/booking` 的接口说明。
5. 可选：新增 GitHub Actions CI（`actions/setup-python` + `pip install -r requirements.txt` + `pytest`），实现“测试与构建通过”。

## 5. 依赖清单（冗余检查）

| 依赖 | 使用情况 | 建议 |
|---|---|---|
| langchain / langchain-core / langchain-openai | 使用（agent、tools、parser） | 保留 |
| google-api-python-client / google-auth-httplib2 / google-auth-oauthlib | 使用（Google Calendar 可选集成） | 保留 |
| python-dotenv | 使用 | 保留 |
| pytest | 测试 | 保留 |
| tzdata | 使用（Windows zoneinfo） | 保留 |
| fastapi / uvicorn / jinja2 | 使用（Web） | 保留 |
| **langchain-community** | **未使用** | **移除** |
| **python-multipart** | **未使用** | **移除** |

## 6. 开源前必须修复的问题（验收门槛）

- [ ] C1 `POST /api/booking` 后端实现，快速预约可用
- [ ] C2 预约日期按用户请求处理，不再总是“明天”
- [ ] C3 `/bookings` 鉴权
- [ ] 删除 4 个伪测试文件，补齐真实测试，`pytest` 通过
- [ ] 删除脚本渲染截图（screen-*、demo.png 替换），提交/补拍真实截图
- [ ] 无敏感信息入库（已满足，保持）
- [ ] README 效果图与运行说明与实际一致