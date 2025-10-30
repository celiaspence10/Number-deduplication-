#!/usr/bin/env python3

import os
import sys

def main() -> int:
    base_dir = os.path.dirname(__file__)
    print("[SelfCheck] Working dir:", base_dir)
    # 1) Python version
    print("[SelfCheck] Python:", sys.version.replace("\n", " "))

    # 2) Tkinter availability
    try:
        import tkinter  # noqa: F401
        print("[SelfCheck] Tkinter: OK")
    except Exception as e:
        print("[SelfCheck] Tkinter: FAIL:", e)
        return 2

    # 3) Core module import
    try:
        import dedupe_us_numbers as core  # noqa: F401
        print("[SelfCheck] Core module: OK")
    except Exception as e:
        print("[SelfCheck] Core module: FAIL:", e)
        return 3

    # 4) Basic normalization test
    from dedupe_us_numbers import normalize_us_number
    ok, e164 = normalize_us_number("(415) 555-0123")
    print("[SelfCheck] Normalize sample:", ok, e164)
    if not ok or not e164.startswith("+1"):
        print("[SelfCheck] Normalize check failed")
        return 4

    print("[SelfCheck] All good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


