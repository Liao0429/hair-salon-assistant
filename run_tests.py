# -*- coding: utf-8 -*-
"""并行运行项目测试：单元测试 + Web 接口测试 + 对话测试，生成报告到 docs/。"""
import subprocess, os, sys, time, json, urllib.request, re
from concurrent.futures import ThreadPoolExecutor

BASE = r"G:\hair-salon-assistant"
VENV_PY = os.path.join(BASE, ".venv", "Scripts", "python.exe")
DOCS = os.path.join(BASE, "docs")
os.makedirs(DOCS, exist_ok=True)

# 干净环境：避免被 Hermes 的 PYTHONPATH 污染
CLEAN_ENV = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV")}


def run_cmd(cmd, cwd=BASE, timeout=300):
    r = subprocess.run(cmd, cwd=cwd, env=CLEAN_ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def test_unit():
    code, out = run_cmd([VENV_PY, "-m", "pytest", "-q"], timeout=400)
    m = re.search(r"(\d+) passed", out)
    passed = m.group(1) if m else "?"
    m2 = re.search(r"(\d+) failed", out)
    failed = m2.group(1) if m2 else "0"
    report = (
        "# 单元测试结果\n\n"
        "命令: .venv/Scripts/python.exe -m pytest -q\n"
        f"退出码: {code}\n"
        f"通过: {passed} | 失败: {failed}\n\n"
        "```\n" + out[-2000:] + "\n```\n"
    )
    with open(os.path.join(DOCS, "TEST_RESULT.md"), "w", encoding="utf-8") as f:
        f.write(report)
    return code, passed, failed


def test_web():
    proc = subprocess.Popen(
        [VENV_PY, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BASE, env=CLEAN_ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    results = {}
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=30) as resp:
            results["health"] = (resp.status, resp.read().decode()[:200])
        with urllib.request.urlopen("http://127.0.0.1:8000/", timeout=30) as resp:
            html = resp.read().decode()
            results["index"] = (resp.status, "Daisy Salon" in html)
        body = json.dumps({"message": "What services do you offer?"}).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:8000/api/chat", data=body,
                                     method="POST", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            results["chat"] = (resp.status, data.get("reply", "")[:200])
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
    report = "# Web 接口测试结果\n\n"
    report += f"- GET /api/health: {results.get('health')}\n"
    report += f"- GET /: {results.get('index')}\n"
    report += f"- POST /api/chat: {results.get('chat')}\n"
    with open(os.path.join(DOCS, "WEB_TEST_RESULT.md"), "w", encoding="utf-8") as f:
        f.write(report)
    return results


def test_live():
    code, out = run_cmd([VENV_PY, "examples/live_test.py"], timeout=240)
    report = (
        "# 对话测试结果\n\n"
        "命令: .venv/Scripts/python.exe examples/live_test.py\n"
        f"退出码: {code}\n\n"
        "```\n" + out[-2000:] + "\n```\n"
    )
    with open(os.path.join(DOCS, "LIVE_TEST_RESULT.md"), "w", encoding="utf-8") as f:
        f.write(report)
    return code, out[-300:]


if __name__ == "__main__":
    print("开始并行测试（单元 + Web + 对话）...")
    with ThreadPoolExecutor(max_workers=3) as ex:
        f1 = ex.submit(test_unit)
        f2 = ex.submit(test_web)
        f3 = ex.submit(test_live)
        r1 = f1.result()
        r2 = f2.result()
        r3 = f3.result()
    print("单元测试:", r1)
    print("Web 测试:", r2)
    print("对话测试:", r3[0])
    print("全部完成，报告已生成到 docs/")