# -*- coding: utf-8 -*-
"""View local bookings stored in SQLite (booking.db).

Usage:
    env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV .venv/Scripts/python.exe view_bookings.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bookinggpt.storage import list_bookings


def main():
    bookings = list_bookings()
    if not bookings:
        print("暂无预约记录（booking.db 为空）。")
        return
    print(f"共 {len(bookings)} 条预约：\n")
    for b in bookings:
        print(
            f"  [{b['status']}] {b['event_time']} | {b['customer_name']} | "
            f"{b['service']} | code={b['booking_code']} | 电话:{b['phone']}"
        )


if __name__ == "__main__":
    main()
