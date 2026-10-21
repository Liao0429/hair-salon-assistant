# Web 接口测试结果

基于 FastAPI `TestClient` 的端到端验证（不调用真实 LLM / Google Calendar）：

- `GET /api/health` → `200 {"status": "ok"}`
- `GET /` → `200`（Daisy Salon 聊天界面）
- `POST /api/booking`（快速预约）→ `200` 返回 `booking_code`；缺 `name`/`date` 返回 `400`；时间格式错误返回 `400`
- `POST /api/chat` → 消息过长返回 `400`；触发限流返回 `429`
- `GET /bookings` → 未设置 `ADMIN_TOKEN` 返回 `503`；token 错误返回 `401`；token 正确返回 `200`

对应测试：`tests/test_api.py`（14 项）。
