#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看本地预约列表（SQLite booking.db）。

用法:
    python view_bookings.py                           # 全部预约（表格）
    python view_bookings.py --status confirmed        # 只看已确认
    python view_bookings.py --status cancelled        # 只看已取消
    python view_bookings.py --search 张                # 按姓名/电话/服务模糊搜索
    python view_bookings.py --service "Hair cut"      # 按服务精确筛选
    python view_bookings.py --code ABC123             # 按 booking code 查详情
    python view_bookings.py --date 2026-10-22         # 按日期筛选（YYYY-MM-DD）
    python view_bookings.py --today                   # 只看今天的预约

示例:
    env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV .venv/Scripts/python.exe view_bookings.py --status confirmed
"""
import sys
import os
import argparse
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookinggpt.storage import list_bookings

STATUS_ICON = {"confirmed": "✅", "cancelled": "❌", "completed": "✔️"}


def match_booking(b, args):
    """根据命令行参数判断预约是否匹配筛选条件。"""
    if args.status and b["status"] != args.status:
        return False
    if args.service and args.service.lower() not in b["service"].lower():
        return False
    if args.code and b["booking_code"].lower() != args.code.lower():
        return False
    if args.date:
        if not b["event_time"] or not b["event_time"].startswith(args.date):
            return False
    if args.today:
        today = date.today().isoformat()
        if not b["event_time"] or not b["event_time"].startswith(today):
            return False
    if args.search:
        haystack = " ".join([b.get("customer_name", ""), b.get("phone", ""),
                             b.get("service", ""), b.get("booking_code", "")]).lower()
        if args.search.lower() not in haystack:
            return False
    return True


def print_table(bookings):
    """以对齐的表格形式打印预约。"""
    if not bookings:
        print("暂无匹配的预约记录。")
        return

    headers = ["状态", "预约时间", "姓名", "服务", "电话", "预约码"]
    rows = []
    for b in bookings:
        icon = STATUS_ICON.get(b["status"], "❓")
        rows.append([
            f"{icon} {b['status']}",
            b["event_time"] or "-",
            b["customer_name"] or "-",
            b["service"] or "-",
            b["phone"] or "-",
            b["booking_code"] or "-",
        ])

    # 计算每列宽度（至少等于表头宽度）
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    def fmt(row):
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    print(fmt(headers))
    print("-+-".join("-" * w for w in widths))
    for r in rows:
        print(fmt(r))


def main():
    parser = argparse.ArgumentParser(description="查看本地预约列表（SQLite booking.db）")
    parser.add_argument("--status", choices=["confirmed", "cancelled", "completed"],
                        help="按状态筛选")
    parser.add_argument("--search", help="按姓名/电话/服务/预约码模糊搜索")
    parser.add_argument("--service", help="按服务名称筛选（不区分大小写）")
    parser.add_argument("--code", help="按预约码查询详情")
    parser.add_argument("--date", help="按日期筛选（YYYY-MM-DD）")
    parser.add_argument("--today", action="store_true", help="只看今天的预约")
    parser.add_argument("--no-color", action="store_true", help="不显示 emoji 图标")
    args = parser.parse_args()

    all_bookings = list_bookings()
    matched = [b for b in all_bookings if match_booking(b, args)]

    print(f"共 {len(matched)} 条预约（总 {len(all_bookings)} 条）\n")
    print_table(matched)


if __name__ == "__main__":
    main()
